import pickle
import asyncio

from api.core.logger import logger
from api.schemas.packet_data import PacketData
from api.services.packet_processor import PacketProcessor
from api.utils.rabbitmq import RabbitMQClient


class ProxyPacketProcessor:
    def __init__(self):
        self.packet_processor = None
        self.client = None
        self.consume_channel = None
        self.produce_channel = None
        self.consumer_tag = None

    async def start_consuming(
            self, udp_timeout: int,
            queue_name='sniffer_svc.raw_packets.processor',
            callback=None,
    ):
        try:
            logger.debug(f"Starting to consume from queue: {queue_name}")
            self.client = RabbitMQClient()
            self.consume_channel = await self.client.get_channel()
            self.produce_channel = await self.client.create_channel()

            self.packet_processor = PacketProcessor(
                proxy_mode=True,
                channel=self.produce_channel,
                udp_timeout=udp_timeout
            )

            await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.consume_channel.queue_declare(queue=queue_name, durable=True)
            )

            def on_message(channel, method, properties, body):
                try:
                    logger.debug("Message received; dispatching to callback")
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
            logger.debug("Consumer started successfully")
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.debug("Consumer task cancelled by signal")
            await self._cleanup()
            raise
        except Exception as e:
            logger.debug(f"Unexpected error in consumer: {e}", exc_info=True)
            await self._cleanup()
            raise

    async def _cleanup(self):
        logger.info("Cleaning up consumer resources")
        if self.consume_channel and self.consumer_tag:
            self.consume_channel.basic_cancel(self.consumer_tag)
            logger.debug("Consumer tag cancelled")

        if self.produce_channel and not self.produce_channel.is_closed:
            await asyncio.get_running_loop().run_in_executor(
                None, self.produce_channel.close
            )
            logger.debug("Producer channel closed")

        if self.client:
            await self.client.close()
            logger.debug("RabbitMQ client connection closed")

    async def packet_processing_callback(self, data):
        try:
            logger.debug("Starting packet deserialization and processing")
            packet_data = pickle.loads(data)
            packet_data = PacketData.from_bytes(packet_data)
            self.packet_processor.process_packet(packet_data)
            logger.debug(f"Packet {packet_data} processed successfully")
        except Exception as e:
            logger.debug(f"Error in packet processing callback: {e}", exc_info=True)
