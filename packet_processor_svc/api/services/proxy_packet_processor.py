import pickle
import asyncio

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
        self,  udp_timeout: int,
        queue_name='sniffer_svc.raw_packets.processor',
        callback=None,
    ):
        try:
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
                    asyncio.create_task(callback(body))
                except Exception as e:
                    print(f"Error processing message: {e}")
                finally:
                    channel.basic_ack(delivery_tag=method.delivery_tag)

            self.consume_channel.basic_qos(prefetch_count=1)
            self.consumer_tag = self.consume_channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message,
                auto_ack=False
            )

            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            print("Consumer task cancellation received")
            await self._cleanup()
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            await self._cleanup()
            raise

    async def _cleanup(self):
        if self.consume_channel and self.consumer_tag:
            self.consume_channel.basic_cancel(self.consumer_tag)

        # Закрытие каналов
        if self.produce_channel and not self.produce_channel.is_closed:
            await asyncio.get_running_loop().run_in_executor(
                None, self.produce_channel.close
            )

        if self.client:
            await self.client.close()

    async def packet_processing_callback(self, raw_packet):
        try:
            packet = pickle.loads(raw_packet)
            self.packet_processor.process_packet(packet)
            # print(f"{packet[IP].src} -> {packet[IP].dst}")
        except Exception as e:
            print(f"Error in packet processing: {e}")
