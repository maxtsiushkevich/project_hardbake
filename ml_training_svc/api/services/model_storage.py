import logging
import sqlite3
from typing import Optional
import numpy as np
from pydantic import ValidationError
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.svm import OneClassSVM

from api.core.logger import logger
from api.exceptions.exceptions import NotEnoughTrainingRecords, ModelsNotReady, InvalidHyperparametersError, \
    UpdateMinSamplesException
from api.schemas.data_record import DataRecord
from api.schemas.ml import TrainingStatus, ModelHyperparameters


class ModelStorage:
    def __init__(self, db_path: str = './db/training_data.db'):
        self.isolation_forest: Optional[IsolationForest] = None
        self.one_class_svm: Optional[OneClassSVM] = None
        self.training_status: TrainingStatus = TrainingStatus.NOT_STARTED
        self.min_samples_for_training: int = 100
        self.hyperparameters: ModelHyperparameters = ModelHyperparameters()

        self.db_path = db_path
        self._init_db()

    async def update_hyperparameters(self, new_hyperparameters: dict):
        try:
            validated_params = ModelHyperparameters(**new_hyperparameters)
            self.hyperparameters = validated_params
            logger.debug("Hyperparameters updated successfully")
        except ValidationError as e:
            logger.debug(f"Invalid hyperparameters: {str(e)}", exc_info=True)
            raise InvalidHyperparametersError(f"Invalid hyperparameters: {str(e)}")
        except Exception as e:
            logger.debug(f"Failed to update hyperparameters: {str(e)}", exc_info=True)
            raise InvalidHyperparametersError(f"Failed to update hyperparameters: {str(e)}")

    async def update_min_samples(self, min_samples: int):
        if min_samples < 0 or min_samples < 100:
            logger.debug("Attempted to update min_samples with invalid value")
            raise UpdateMinSamplesException("Minimum samples must be >= 100")
        self.min_samples_for_training = min_samples
        logger.debug(f"Minimum samples for training updated to {min_samples}")

        self.min_samples_for_training = min_samples

    async def get_current_settings(self):
        logger.debug("Retrieving current model settings")
        return {
            "hyperparameters": self.hyperparameters,
        }

    async def get_training_status(self):
        logger.debug("Retrieving training status")
        return {
            "training_status": self.training_status,
            "collected_samples": self.get_len_of_training_data(),
            "min_samples_for_training": self.min_samples_for_training
        }

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    protocol INTEGER,
                    bwd_packet_length_max INTEGER,
                    bwd_packet_length_min INTEGER,
                    bwd_packet_length_mean REAL,
                    bwd_packet_length_std REAL,
                    flow_IAT_std REAL,
                    flow_IAT_max INTEGER,
                    fwd_IAT_std REAL,
                    fwd_IAT_max INTEGER,
                    min_packet_length INTEGER,
                    max_packet_length INTEGER,
                    packet_length_std REAL,
                    packet_length_variance REAL,
                    psh_flag_count INTEGER,
                    avg_bwd_segment_size REAL,
                    idle_min INTEGER,
                    idle_mean REAL,
                    idle_max INTEGER
                )
            ''')
            conn.commit()
            conn.close()
            logger.debug("Initialized training_data database")
        except Exception as e:
            logger.debug(f"Failed to initialize database: {str(e)}", exc_info=True)

    def add_data(self, data: DataRecord):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO training_data (
                    protocol, bwd_packet_length_max, bwd_packet_length_min, bwd_packet_length_mean,
                    bwd_packet_length_std, flow_IAT_std, flow_IAT_max, fwd_IAT_std, fwd_IAT_max,
                    min_packet_length, max_packet_length, packet_length_std, packet_length_variance,
                    psh_flag_count, avg_bwd_segment_size, idle_min, idle_mean, idle_max
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.protocol, data.bwd_packet_length_max, data.bwd_packet_length_min,
                data.bwd_packet_length_mean, data.bwd_packet_length_std, data.flow_IAT_std,
                data.flow_IAT_max, data.fwd_IAT_std, data.fwd_IAT_max, data.min_packet_length,
                data.max_packet_length, data.packet_length_std, data.packet_length_variance,
                data.psh_flag_count, data.avg_bwd_segment_size, data.idle_min, data.idle_mean,
                data.idle_max
            ))
            conn.commit()
            conn.close()
            logger.debug("Data record added to database")
        except Exception as e:
            logger.debug(f"Failed to add data to database: {str(e)}", exc_info=True)

    def _get_training_data(self) -> np.ndarray:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT 
                    protocol, bwd_packet_length_max, bwd_packet_length_min, bwd_packet_length_mean,
                    bwd_packet_length_std, flow_IAT_std, flow_IAT_max, fwd_IAT_std, fwd_IAT_max,
                    min_packet_length, max_packet_length, packet_length_std, packet_length_variance,
                    psh_flag_count, avg_bwd_segment_size, idle_min, idle_mean, idle_max
                FROM training_data
                ORDER BY id DESC
                LIMIT ?
            ''', (self.min_samples_for_training,))
            data = cursor.fetchall()
            conn.close()
            data.reverse()
            logger.debug(f"Fetched {len(data)} records for training")
            data_np = np.array(data, dtype=np.float32)
            scaler = RobustScaler()
            return scaler.fit_transform(data_np)
        except Exception as e:
            logger.debug(f"Error fetching training data: {str(e)}", exc_info=True)
            raise

    async def train_models(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                count = conn.execute('SELECT COUNT(*) FROM training_data').fetchone()[0]

            if count < self.min_samples_for_training:
                logger.debug("Not enough training data to start training")
                raise NotEnoughTrainingRecords

            self.training_status = TrainingStatus.TRAINING
            logger.debug("Training started")
            X = self._get_training_data()

            self.isolation_forest = IsolationForest(**self.hyperparameters.isolation_forest)
            outliers = self.isolation_forest.fit_predict(X)
            normal_data = X[outliers == 1]

            if len(normal_data) > 0:
                self.one_class_svm = OneClassSVM(**self.hyperparameters.one_class_svm)
                self.one_class_svm.fit(normal_data)
                self.training_status = TrainingStatus.READY
                logger.debug("Model training completed successfully")
            else:
                self.training_status = TrainingStatus.ERROR
                logger.debug("No normal data found after Isolation Forest filtering")
        except Exception as e:
            self.training_status = TrainingStatus.ERROR
            logger.debug(f"Model training failed: {str(e)}", exc_info=True)
            raise

    def save_models(self, path: str):
        import joblib
        try:
            if self.training_status != TrainingStatus.READY:
                logger.debug("Attempted to save models before training was complete")
                raise ModelsNotReady()
            joblib.dump({
                'isolation_forest': self.isolation_forest,
                'one_class_svm': self.one_class_svm
            }, path)
            logger.debug(f"Models saved to {path}")
        except Exception as e:
            logger.debug(f"Failed to save models: {str(e)}", exc_info=True)
            raise


    def load_models(self, path: str):
        import joblib
        try:
            models = joblib.load(path)
            self.isolation_forest = models['isolation_forest']
            self.one_class_svm = models['one_class_svm']
            self.training_status = TrainingStatus.READY
            logger.debug(f"Models loaded from {path}")
        except Exception as e:
            logger.debug(f"Failed to load models: {str(e)}", exc_info=True)
            raise


    def get_len_of_training_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM training_data')
            count = cursor.fetchone()[0]
            conn.close()
            logger.debug(f"Training data sample count: {count}")
            return count
        except Exception as e:
            logger.debug(f"Failed to count training data: {str(e)}", exc_info=True)
            return 0