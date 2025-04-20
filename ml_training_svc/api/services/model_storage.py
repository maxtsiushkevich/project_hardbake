import asyncio
import logging
import sqlite3
from typing import Optional, List
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from sklearn.svm import OneClassSVM

from api.schemas.data_record import DataRecord
from api.schemas.ml import TrainingStatus, ModelHyperparameters
from exceptions.exceptions import ModelsNotReady, NotEnoughTrainingRecords


class ModelStorage:
    def __init__(self, db_path: str = 'training_data.db'):
        self.isolation_forest: Optional[IsolationForest] = None
        self.one_class_svm: Optional[OneClassSVM] = None
        self.training_status: TrainingStatus = TrainingStatus.NOT_STARTED
        self.min_samples_for_training: int = 100000
        self.hyperparameters: ModelHyperparameters = ModelHyperparameters()

        # Initialize database
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with the appropriate table structure."""
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

    def add_data(self, data: DataRecord):
        """Add a new data record to the SQLite database."""
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

    def _get_training_data(self) -> np.ndarray:
        """Retrieve the last n records from the database and convert to numpy array."""
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

        data_np = np.array(data, dtype=np.float32)

        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(data_np)

        return scaled_data

    async def train_models(self):
        print('start')
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute('SELECT COUNT(*) FROM training_data').fetchone()[0]

        if count >= self.min_samples_for_training:
            try:
                self.training_status = TrainingStatus.TRAINING
                X = self._get_training_data()

                # Train Isolation Forest
                self.isolation_forest = IsolationForest(
                    **self.hyperparameters.isolation_forest
                )
                outliers = self.isolation_forest.fit_predict(X)

                # Filter normal data for OneClassSVM
                normal_data = X[outliers == 1]

                if len(normal_data) > 0:
                    # Train OneClassSVM
                    self.one_class_svm = OneClassSVM(
                        **self.hyperparameters.one_class_svm
                    )
                    self.one_class_svm.fit(normal_data)
                    self.training_status = TrainingStatus.READY
                else:
                    self.training_status = TrainingStatus.ERROR
                    logging.error("No normal data found after Isolation Forest filtering")

            except Exception as e:
                self.training_status = TrainingStatus.ERROR
                logging.error(f"Error during model training: {str(e)}")
                raise
        else:
            raise NotEnoughTrainingRecords
        print('goaaaal')

    def save_models(self, path: str):
        """Save trained models to disk."""
        import joblib
        try:
            if self.training_status == TrainingStatus.READY:
                joblib.dump({
                    'isolation_forest': self.isolation_forest,
                    'one_class_svm': self.one_class_svm
                }, path)
            else:
                raise ModelsNotReady()
        except Exception as e:
            logging.error(f"Error saving models: {str(e)}")
            raise

    def load_models(self, path: str):
        """Load trained models from disk."""
        import joblib
        try:
            models = joblib.load(path)
            self.isolation_forest = models['isolation_forest']
            self.one_class_svm = models['one_class_svm']
            self.training_status = TrainingStatus.READY
        except Exception as e:
            logging.error(f"Error loading models: {str(e)}")
            raise

    def get_len_of_training_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM training_data')
        count = cursor.fetchone()[0]
        conn.close()
        return count