import pickle
import asyncio

from scapy.layers.inet import IP

from api.utils.rabbitmq import RabbitMQClient


async def consume_raw_packets(queue_name='sniffer_svc.raw_packets.processor', callback=None):
    client = None
    try:
        client = RabbitMQClient()
        channel = await client.get_channel()

        await asyncio.get_running_loop().run_in_executor(
            None,
            channel.queue_declare,
            queue_name,
            True
        )

        def on_message(channel, method, properties, body):
            try:
                asyncio.create_task(callback(body))
            except Exception as e:
                print(f"Error processing message: {e}")
            finally:
                channel.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_qos(prefetch_count=1)
        consumer_tag = channel.basic_consume(
            queue='sniffer_svc.raw_packets.processor',
            on_message_callback=on_message,
            auto_ack=False
        )

        print(f" [*] Waiting for messages. To exit press CTRL+C")

        # Ждем отмены задачи
        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        print("Consumer task cancellation received")
        if client and channel:
            channel.basic_cancel(consumer_tag)
            await client.close()
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        if client:
            await client.close()
        raise


async def packet_processing_callback(raw_packet):
    try:
        # Process the raw packet here
        packet = pickle.loads(raw_packet)
        print(f"{packet[IP].src} = {packet[IP].dst}")

    except Exception as e:
        print(f"Error in packet processing: {e}")









