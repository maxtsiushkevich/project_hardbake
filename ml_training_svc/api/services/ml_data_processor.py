import logging
import pickle

from api.schemas.data_record import DataRecord
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient


class MLDataProcessor:
    def __init__(self, rabbitmq_client: RabbitMQClient, model_storage: ModelStorage):
        self.rabbitmq_client = rabbitmq_client
        self.model_storage = model_storage
        self.consuming = False
        self.queue_name = "ml_data_processor_svc.ml_data.training"
        self.consumer_tag = None
        self.channel = None

    async def start_consuming(self):
        if self.consuming:
            return

        self.consuming = True
        self.channel = await self.rabbitmq_client.get_channel()

        self.consumer_tag = self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.process_message,
            auto_ack=True
        )

    def process_message(self, channel, method, properties, body):
        try:
            print('yes')
            data_record: DataRecord = pickle.loads(body)

            self.model_storage.add_data(data_record)

            if self.model_storage.get_len_of_training_data() >= self.model_storage.min_samples_for_training:
                self.start_consuming()

        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")

    async def stop_consuming(self):
        if self.consuming and self.consumer_tag:
            channel = await self.rabbitmq_client.get_channel()
            try:
                channel.basic_cancel(self.consumer_tag)
                print("Stopped consuming")
                self.channel.close()
            except Exception as e:
                print(f"Failed to cancel consumer: {e}")
        self.consuming = False
