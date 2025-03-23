import os
from dotenv import load_dotenv

import pika
from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer

from api.core.context import sniffers
from api.repository.redis_repository import RedisRepository
from api.schemas.sniffer import SniffStatus


class RabbitMQClient:

    def __init__(self):

        load_dotenv()
        self.host = os.getenv("RABBITMQ_HOST")
        self.queue = os.getenv("RABBITMQ_QUEUE")

        self.connection = None
        self.channel = None
        self.connect()

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, durable=True)
        except Exception as e:
            print(f"Ошибка подключения к RabbitMQ: {e}")
            self.connection = None
            self.channel = None

    def send(self, raw_packet: bytes):
        if not self.channel or self.connection.is_closed:
            self.connect()
        if self.channel:
            try:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=raw_packet,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            except Exception as e:
                print(f"Ошибка при отправке в RabbitMQ: {e}")
                self.connect()
        else:
            print("Соединение с RabbitMQ отсутствует. Пакет не отправлен.")


rabbit_client = RabbitMQClient()


def packet_operator(packet):
    raw_packet = bytes(packet)
    print(raw_packet)
    rabbit_client.send(raw_packet)


async def sniff_task(sniff_id: UUID, iface: str, filters: str | None, redis: RedisRepository):
    try:
        sniffer = AsyncSniffer(iface=iface, prn=packet_operator, filter=filters)
        sniffer.start()
        sniffers[sniff_id] = sniffer
    except Exception as e:
        await redis.update_sniff(sniff_id, SniffStatus.Crashed)
        raise
