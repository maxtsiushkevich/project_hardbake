import asyncio

from api.core.logger import logger
from api.exceptions.exceptions import RabbitMQError
from api.schemas.data_record import DataRecord
from api.schemas.schemas import ConsumingStatusEnum
from api.services.data_storage import add_data_record
from api.utils.database import get_db
# from api.services.detection_service import DetectionService
from api.utils.rabbitmq import RabbitMQClient


class ConsumerManager:
    def __init__(self, rabbitmq_client: RabbitMQClient):
        self.rabbitmq_client = rabbitmq_client
        self.consuming = False
        self.queue_name = "threat_detection_svc.notification.notification"
        self.consumer_tag = None
        self.channel = None

        self.status: ConsumingStatusEnum = ConsumingStatusEnum.NOT_RUNNING

    async def start(self):
        if self.consuming:
            logger.debug("ConsumerManager already running")
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
            self.status = ConsumingStatusEnum.RUNNING
            logger.debug("ConsumerManager started and consuming messages")
        except RabbitMQError as e:
            self.status = ConsumingStatusEnum.ERROR
            logger.debug(f"Failed to start ConsumerManager due to RabbitMQError: {e}", exc_info=True)
            raise e

    def process_message_wrapper(self, channel, method, properties, body):
        asyncio.create_task(self.process_message(channel, method, properties, body))

    async def process_message(self, channel, method, properties, body):
        try:
            data_record = DataRecord.model_validate_json(body)
            logger.debug(f"Processing data record: {data_record}")

            with get_db() as db:
                add_data_record(data_record, db)

            logger.debug("Data record processed and added to database")

        except RabbitMQError as e:
            self.status = ConsumingStatusEnum.ERROR
            logger.debug(f"RabbitMQError while processing message: {e}", exc_info=True)
            raise e
        except Exception as e:
            self.status = ConsumingStatusEnum.ERROR
            logger.debug(f"Unexpected error while processing message: {e}", exc_info=True)
            raise e

    async def stop(self):
        if self.consuming and self.consumer_tag:
            try:
                self.channel.basic_cancel(self.consumer_tag)
                print("Stopped consuming")
                self.status = ConsumingStatusEnum.STOPPED
                logger.debug("ConsumerManager stopped successfully")
            except RabbitMQError as e:
                self.status = ConsumingStatusEnum.ERROR
                logger.debug(f"Failed to stop ConsumerManager due to RabbitMQError: {e}", exc_info=True)
                raise e

        self._cleanup()
        self.consuming = False

    def _cleanup(self):
        self.consuming = False
        self.consumer_tag = None
        self.channel = None

    def get_status(self):
        try:
            if not self.rabbitmq_client._connection or self.rabbitmq_client._connection.is_closed:
                if self.status == ConsumingStatusEnum.RUNNING:
                    self._cleanup()
                    self.status = ConsumingStatusEnum.ERROR
        except Exception as e:
            logger.error(f"Error checking RabbitMQ connection state: {str(e)}")
            self._cleanup()
            self.status = ConsumingStatusEnum.ERROR
        logger.debug(f"Consumer status queried: {self.status}")
        return self.status

