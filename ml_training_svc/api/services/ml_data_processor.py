from api.core.logger import logger
from api.schemas.data_record import DataRecord
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient


class MLDataProcessor:
    def __init__(self, model_storage: ModelStorage):
        self.rabbitmq_client = RabbitMQClient()
        self.model_storage = model_storage
        self.consuming = False
        self.queue_name = "ml_data_processor_svc.ml_data.training"
        self.consumer_tag = None
        self.channel = None

    async def start_consuming(self):
        if self.consuming:
            logger.debug("Consuming already started")
            return

        logger.debug(f"Starting to consume from queue: {self.queue_name}")
        try:
            self.consuming = True
            self.channel = await self.rabbitmq_client.get_channel()

            self.consumer_tag = self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message,
                auto_ack=True
            )

            logger.debug("Consumer started successfully")
        except Exception as e:
            logger.debug(f"Failed to start consuming: {e}", exc_info=True)
            self.consuming = False

    def process_message(self, channel, method, properties, body):
        try:
            data_record = DataRecord.model_validate_json(body)
            logger.debug(f"Process message {data_record}")

            self.model_storage.add_data(data_record)
        except Exception as e:
            logger.debug(f"Error processing message: {str(e)}", exc_info=True)

    async def stop_consuming(self):
        logger.debug("Stopping message consuming received")
        if self.consuming and self.consumer_tag:
            try:
                channel = await self.rabbitmq_client.get_channel()
                channel.basic_cancel(self.consumer_tag)
                logger.debug("Consumer stopped successfully")
                self.channel.close()
            except Exception as e:
                logger.debug(f"Failed to stop consumer: {e}", exc_info=True)
        else:
            logger.debug("No active consumer was found")

        self.consuming = False