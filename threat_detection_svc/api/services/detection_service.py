from typing import Optional, List
import numpy as np
import pika
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM

from api.core.logger import logger
from api.exceptions.exceptions import ModelUploadError
from api.schemas.data_record import DataRecord
from api.utils.rabbitmq import RabbitMQClient


class DetectionService:
    def __init__(self):
        self.isolation_forest: Optional[IsolationForest] = None
        self.one_class_svm: Optional[OneClassSVM] = None

        self.batch_size: int = 1_000
        self._current_batch: List[DataRecord] = []

        self.rabbitmq_client = RabbitMQClient()

    def load_models(self, path: str):
        import joblib
        try:
            logger.debug(f"Loading models from {path}")
            models = joblib.load(path)
            self.isolation_forest = models['isolation_forest']
            self.one_class_svm = models['one_class_svm']
            logger.debug("Models loaded successfully")
        except Exception as e:
            logger.debug(f"Error loading models from {path}: {e}", exc_info=e)
            raise ModelUploadError(f"Error loading models: {str(e)}")

    async def set_batch_size(self, size: int):
        if size <= 100:
            logger.debug(f"Attempted to set invalid batch size: {size}")
            raise ValueError("Minimum batch size is 100")
        logger.debug(f"Batch size updated to {size}")
        self.batch_size = size

    async def get_batch_size(self):
        logger.debug(f"Retrieving batch size: {self.batch_size}")
        return self.batch_size

    async def add_data(self, data: DataRecord):
        self._current_batch.append(data)
        logger.debug(f"Added data to batch, current size: {len(self._current_batch)}")
        if len(self._current_batch) >= self.batch_size:
            logger.debug("Batch size threshold reached, processing batch")
            await self.process_batch()

    async def process_batch(self):
        if not self._current_batch:
            logger.debug("No data to process in batch")
            return
        if not self.isolation_forest or not self.one_class_svm:
            logger.debug("Models not loaded; skipping batch processing")
            return

        try:
            features = self._convert_to_features()
            logger.debug("Converted batch to feature matrix")

            if_anomalies = self.isolation_forest.predict(features)
            svm_anomalies = self.one_class_svm.predict(features)

            combined_anomalies = (if_anomalies == -1) & (svm_anomalies == -1)

            logger.debug(f"Anomalies: {combined_anomalies}")

            await self._handle_anomalies(self._current_batch, combined_anomalies)

            logger.debug(f"Processed batch of size {len(self._current_batch)}")
        except Exception as e:
            logger.debug(f"Error processing batch: {e}", exc_info=e)
        finally:
            self._current_batch = []

    def _convert_to_features(self) -> np.ndarray:
        """Convert batch of DataRecords to numpy feature matrix"""
        features = []
        for record in self._current_batch:
            feature_vector = [
                record.protocol,
                record.bwd_packet_length_max,
                record.bwd_packet_length_min,
                record.bwd_packet_length_mean,
                record.bwd_packet_length_std,
                record.flow_IAT_std,
                record.flow_IAT_max,
                record.fwd_IAT_std,
                record.fwd_IAT_max,
                record.min_packet_length,
                record.max_packet_length,
                record.packet_length_std,
                record.packet_length_variance,
                record.psh_flag_count,
                record.avg_bwd_segment_size,
                record.idle_min,
                record.idle_mean,
                record.idle_max,
            ]
            features.append(feature_vector)
        logger.debug(f"Converted {len(features)} records to feature vectors")
        return np.array(features)

    async def _handle_anomalies(self, batch: List[DataRecord], anomalies: np.ndarray):
        try:
            channel = await self.rabbitmq_client.get_channel()
            logger.debug("Acquired RabbitMQ channel for anomaly notifications")

            for record, is_anomaly in zip(batch, anomalies):
                if is_anomaly:
                    try:
                        channel.basic_publish(
                            exchange='threat_detection_svc.notification.fanout',
                            routing_key='',
                            body=record.model_dump_json(),
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
                        logger.debug(f"Anomaly published for flow")
                    except Exception as e:
                        logger.debug(f"Failed to send anomaly notification for flow: {e}", exc_info=e)
        except Exception as e:
            logger.debug(f"Error handling anomalies: {e}", exc_info=e)