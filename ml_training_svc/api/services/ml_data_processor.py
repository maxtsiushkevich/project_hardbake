from api.core.logger import logger
from api.schemas.data_record import DataRecord
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient
from api.schemas.ml import ConsumerStatusEnum


class MLDataProcessor:
    def __init__(self, model_storage: ModelStorage):
        self.rabbitmq_client = RabbitMQClient()
        self.model_storage = model_storage
        self.consuming = False
        self.queue_name = "ml_data_processor_svc.ml_data.training"
        self.consumer_tag = None
        self.channel = None
        self.consumer_status = ConsumerStatusEnum.NOT_RUNNING

    async def start_consuming(self):
        if self.consuming:
            logger.debug("Consuming already started")
            return

        logger.debug(f"Starting to consume from queue: {self.queue_name}")
        try:
            if self.channel is not None:
                try:
                    await self.channel.close()
                except Exception as e:
                    logger.debug(f"Error closing old channel: {e}", exc_info=True)

            self.consuming = True
            self.channel = await self.rabbitmq_client.get_channel()

            self.consumer_tag = self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message,
                auto_ack=True
            )

            self.consumer_status = ConsumerStatusEnum.RUNNING
            logger.debug("Consumer started successfully")
        except ConnectionError as e:
            logger.error(f"RabbitMQ connection error: {str(e)}")
            self._cleanup()
            self.consumer_status = ConsumerStatusEnum.ERROR
            raise
        except Exception as e:
            logger.error(f"Failed to start consuming: {e}", exc_info=True)
            self._cleanup()
            self.consumer_status = ConsumerStatusEnum.ERROR
            raise

    def _cleanup(self):
        self.consuming = False
        self.consumer_tag = None
        self.channel = None

    def process_message(self, channel, method, properties, body):
        try:
            data_record = DataRecord.model_validate_json(body)
            logger.debug(f"Process message {data_record}")

            self.model_storage.add_data(data_record)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)

    async def stop_consuming(self):
        logger.debug("Stopping message consuming received")
        if self.consuming and self.consumer_tag and self.channel:
            try:
                self.channel.basic_cancel(self.consumer_tag)
                logger.debug("Consumer stopped successfully")
            except Exception as e:
                logger.error(f"Failed to stop consumer: {e}", exc_info=True)

        self.consuming = False
        self._cleanup()
        self.consumer_status = ConsumerStatusEnum.STOPPED
        if self.channel:
            try:
                await self.channel.close()
            except Exception as e:
                logger.error(f"Error closing channel: {e}", exc_info=True)
            finally:
                self.channel = None

    def get_consumer_status(self):
        try:
            if not self.rabbitmq_client._connection or self.rabbitmq_client._connection.is_closed:
                if self.consumer_status == ConsumerStatusEnum.RUNNING:
                    self._cleanup()
                    self.consumer_status = ConsumerStatusEnum.ERROR
        except Exception as e:
            logger.error(f"Error checking RabbitMQ connection state: {str(e)}")
            self._cleanup()
            self.consumer_status = ConsumerStatusEnum.ERROR
        logger.debug(f"Consumer status queried: {self.consumer_status}")
        return self.consumer_status
