import pickle
import asyncio

from api.schemas.packet_data import PacketData
from api.utils.rabbitmq import RabbitMQClient


class StreamProcessor:
    def __init__(self):
        self.client = None
        self.consume_channel = None
        # self.produce_channel = None
        self.consumer_tag = None

    async def start_consuming(
            self, queue_name='packet_processor_svc.processed_packets.ml_dp',
            callback=None,
    ):
        try:
            self.client = RabbitMQClient()
            self.consume_channel = await self.client.get_channel()
            # self.produce_channel = await self.client.create_channel()

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

        # if self.produce_channel and not self.produce_channel.is_closed:
        #     await asyncio.get_running_loop().run_in_executor(
        #         None, self.produce_channel.close
        #     )

        if self.client:
            await self.client.close()

    async def stream_processing_callback(self, data):
        packet_data = pickle.loads(data)
        # problem: 10:ff:e0:63:f4:83 > dc:ef:80:41:a3:f8 (IPv4) / Raw instead Ether / IP / TCP 34.237.73.95:https > 192.168.100.229:51681 PA / Raw for example
        print(packet_data[0].packet.summary())
