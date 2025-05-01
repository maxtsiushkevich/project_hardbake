import pickle
import asyncio

import pika

from api.core.logger import logger
from api.schemas.data_record import DataRecord
from api.schemas.packet_data import PacketData
from api.services.ml_parcer import MLParser
from api.utils.rabbitmq import RabbitMQClient


class StreamProcessor:
    def __init__(self):
        self.client = None
        self.consume_channel = None
        self.produce_channel = None
        self.consumer_tag = None

    async def start_consuming(
            self, queue_name='packet_processor_svc.processed_packets.ml_dp',
            callback=None,
    ):
        logger.debug(f"Starting to consume from queue: {queue_name}")
        try:
            self.client = RabbitMQClient()
            self.consume_channel = await self.client.get_channel()
            self.produce_channel = await self.client.create_channel()

            await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.consume_channel.queue_declare(queue=queue_name, durable=True)
            )
            logger.debug("Queue declared and channels initialized")

            def on_message(channel, method, properties, body):
                try:
                    asyncio.create_task(callback(body))
                except Exception as e:
                    logger.debug(f"Error processing message: {e}", exc_info=True)
                finally:
                    channel.basic_ack(delivery_tag=method.delivery_tag)

            self.consume_channel.basic_qos(prefetch_count=1)
            self.consumer_tag = self.consume_channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message,
                auto_ack=False
            )

            logger.debug("Consumer successfully started")

            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.debug("Consumer task cancellation received")
            await self._cleanup()
            raise
        except Exception as e:
            logger.debug(f"Unexpected error in consumer: {e}", exc_info=True)
            await self._cleanup()
            raise

    async def _cleanup(self):
        logger.debug("Cleaning up RabbitMQ resources")
        if self.consume_channel and self.consumer_tag:
            try:
                self.consume_channel.basic_cancel(self.consumer_tag)
                logger.debug("Consumer tag cancelled")
            except Exception as e:
                logger.debug(f"Failed to cancel consumer tag: {e}", exc_info=True)

        if self.produce_channel and not self.produce_channel.is_closed:
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None, self.produce_channel.close
                )
                logger.debug("Producer channel closed")
            except Exception as e:
                logger.debug(f"Error closing producer channel: {e}", exc_info=True)

        if self.client:
            await self.client.close()
            logger.debug("RabbitMQ client closed")

    async def stream_processing_callback(self, data):
        try:
            logger.debug("Deserializing packet data")
            packet_data = pickle.loads(data)
            stream = [PacketData.from_bytes(d) for d in packet_data]

            logger.debug(f"Processing stream of {len(stream)} packets")
            record: DataRecord = await MLParser.parsing_task(stream)

            if record is None:
                logger.debug("No DataRecord generated from packet stream")
                return

            json_record = record.model_dump_json()

            logger.debug("Publishing processed DataRecord to RabbitMQ")
            self.produce_channel.basic_publish(
                exchange='ml_data_processor_svc.ml_data.fanout',
                routing_key='',
                body=json_record,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.debug("DataRecord published successfully")
        except Exception as e:
            logger.debug(f"Error while sending processed message: {e}", exc_info=True)
            raise