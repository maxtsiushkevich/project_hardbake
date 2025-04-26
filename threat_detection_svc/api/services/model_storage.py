from typing import Optional, List
import numpy as np
import pika
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from api.exceptions.exceptions import ModelUploadError
from api.schemas.data_record import DataRecord
from api.utils.rabbitmq import RabbitMQClient


class ModelStorage:
    def __init__(self):
        self.isolation_forest: Optional[IsolationForest] = None
        self.one_class_svm: Optional[OneClassSVM] = None

        self.batch_size: int = 1_000
        self._current_batch: List[DataRecord] = []

        self.rabbitmq_client = RabbitMQClient()

    def load_models(self, path: str):
        import joblib
        try:
            models = joblib.load(path)
            self.isolation_forest = models['isolation_forest']
            self.one_class_svm = models['one_class_svm']
        except Exception as e:
            raise ModelUploadError(f"Error loading models: {str(e)}")

    async def set_batch_size(self, size: int):
        if size <= 100:
            raise ValueError("Minimum batch size is 100")
        self.batch_size = size

    async def get_batch_size(self):
        return self.batch_size

    async def add_data(self, data: DataRecord):
        self._current_batch.append(data)
        if len(self._current_batch) >= self.batch_size:
            await self.process_batch()

    async def process_batch(self):
        if not self._current_batch or not self.isolation_forest or not self.one_class_svm:
            return

        # Convert batch to feature matrix
        features = self._convert_to_features()

        # Detect anomalies
        if_anomalies = self.isolation_forest.predict(features)
        svm_anomalies = self.one_class_svm.predict(features)

        # Combine results
        combined_anomalies = (if_anomalies == -1) | (svm_anomalies == -1)

        # Process anomalies
        await self._handle_anomalies(self._current_batch, combined_anomalies)

        # Clear current batch
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
        return np.array(features)

    async def _handle_anomalies(self, batch: List[DataRecord], anomalies: np.ndarray):
        """Send detected anomalies to notification service"""
        channel = await self.rabbitmq_client.get_channel()

        for record, is_anomaly in zip(batch, anomalies):
            if is_anomaly:
                try:
                    channel.basic_publish(
                        exchange='threat_detection_svc.notification.fanout',
                        routing_key='',
                        body=record.model_dump_json(),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                except Exception as e:
                    print(f"Failed to send anomaly notification: {e}")