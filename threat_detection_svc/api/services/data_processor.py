import asyncio

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
            return

        try:
            self.channel = await self.rabbitmq_client.get_channel()

            self.consumer_tag = self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message_wrapper,
                auto_ack=True
            )
            self.consuming = True
            self.status = DetectionStatusEnum.RUNNING
        except RabbitMQError as e:
            self.status = DetectionStatusEnum.FAILED
            raise e

    def process_message_wrapper(self, channel, method, properties, body):
        asyncio.create_task(self.process_message(channel, method, properties, body))

    async def process_message(self, channel, method, properties, body):
        try:
            data_record = DataRecord.model_validate_json(body)
            print(data_record)

            await self.model_storage.add_data(data_record)

        except RabbitMQError as e:
            self.status = DetectionStatusEnum.FAILED
            raise e
        except Exception as e:
            self.status = DetectionStatusEnum.FAILED
            raise e

    async def stop(self):
        if self.consuming and self.consumer_tag:
            channel = await self.rabbitmq_client.get_channel()

            try:
                channel.basic_cancel(self.consumer_tag)
                print("Stopped consuming")
                self.channel.close()
                self.status = DetectionStatusEnum.STOPPED
            except RabbitMQError as e:
                self.status = DetectionStatusEnum.FAILED
                raise e

        await self.model_storage.process_batch()
        self.consuming = False

    def get_status(self):
        return self.status
