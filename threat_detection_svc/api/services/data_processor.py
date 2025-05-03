import asyncio

from api.core.logger import logger
from api.exceptions.exceptions import RabbitMQError
from api.schemas.data_record import DataRecord
from api.schemas.detect import DetectionStatusEnum
from api.services.detection_service import DetectionService
from api.utils.rabbitmq import RabbitMQClient


class DataProcessor:
    def __init__(self, rabbitmq_client: RabbitMQClient, model_storage: DetectionService):
        self.rabbitmq_client = rabbitmq_client
        self.model_storage = model_storage
        self.consuming = False
        self.queue_name = "ml_data_processor_svc.ml_data.detection"
        self.consumer_tag = None
        self.channel = None

        self.status: DetectionStatusEnum = DetectionStatusEnum.NOT_RUNNING

    async def start(self):
        if self.consuming:
            logger.debug("DataProcessor already running")
            return

        logger.debug(f"Starting to consume from queue: {self.queue_name}")
        try:
            self.channel = await self.rabbitmq_client.get_channel()

            self.consumer_tag = self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message_wrapper,
                auto_ack=True
            )
            self.consuming = True
            self.status = DetectionStatusEnum.RUNNING
            logger.debug("DataProcessor started and consuming messages")
        except RabbitMQError as e:
            self.status = DetectionStatusEnum.ERROR
            logger.debug(f"Failed to start DataProcessor due to RabbitMQError: {e}", exc_info=True)
            raise e

    def process_message_wrapper(self, channel, method, properties, body):
        asyncio.create_task(self.process_message(channel, method, properties, body))

    async def process_message(self, channel, method, properties, body):
        try:
            data_record = DataRecord.model_validate_json(body)
            logger.debug(f"Processing data record: {data_record}")

            await self.model_storage.add_data(data_record)
            logger.debug("Data record processed and added to model storage")

        except RabbitMQError as e:
            self.status = DetectionStatusEnum.ERROR
            logger.debug(f"RabbitMQError while processing message: {e}", exc_info=True)
            raise e
        except Exception as e:
            self.status = DetectionStatusEnum.ERROR
            logger.debug(f"Unexpected error while processing message: {e}", exc_info=True)
            raise e

    async def stop(self):
        if self.consuming and self.consumer_tag:
            try:
                self.channel.basic_cancel(self.consumer_tag)
                print("Stopped consuming")
                self.status = DetectionStatusEnum.STOPPED
                logger.debug("DataProcessor stopped successfully")
            except RabbitMQError as e:
                self.status = DetectionStatusEnum.ERROR
                logger.debug(f"Failed to stop DataProcessor due to RabbitMQError: {e}", exc_info=True)
                raise e

        self._cleanup()
        await self.model_storage.process_batch()
        self.consuming = False
        logger.debug("Remaining batch data processed after stopping")

    def _cleanup(self):
        self.consuming = False
        self.consumer_tag = None
        self.channel = None

    def get_status(self):
        try:
            if not self.rabbitmq_client._connection or self.rabbitmq_client._connection.is_closed:
                if self.status == DetectionStatusEnum.RUNNING:
                    self._cleanup()
                    self.status = DetectionStatusEnum.ERROR
        except Exception as e:
            logger.error(f"Error checking RabbitMQ connection state: {str(e)}")
            self._cleanup()
            self.status = DetectionStatusEnum.ERROR
        logger.debug(f"Consumer status queried: {self.status}")
        return self.status

