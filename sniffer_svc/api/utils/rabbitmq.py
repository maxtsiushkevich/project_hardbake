import os
import asyncio
import threading
from dotenv import load_dotenv
import pika
from uuid import UUID
from pika.adapters.asyncio_connection import AsyncioConnection


def singleton(class_):
    instances = {}
    instances_lock = threading.Lock()

    def getinstance(*args, **kwargs):
        with instances_lock:
            if class_ not in instances:
                instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class RabbitMQClient:
    _init_lock = threading.Lock()

    def __init__(self):
        with self._init_lock:
            load_dotenv()

            user = os.getenv("RABBITMQ_USER")
            password = os.getenv("RABBITMQ_PASSWORD")
            host = os.getenv("RABBITMQ_HOST")
            port = os.getenv("RABBITMQ_PORT")

            if not all([user, password, host, port]):
                raise ValueError("Missing RabbitMQ configuration in environment variables")

            self._credentials = pika.PlainCredentials(user, password)
            self._connection_params = pika.ConnectionParameters(
                host=host,
                port=int(port),
                credentials=self._credentials,
            )
            self.channels = {}
            self.channels_lock = threading.Lock()
            self._connection = None

            self._connect()

    def _connect(self):
        try:
            self._connection = AsyncioConnection(self._connection_params)
        except Exception as e:
            raise ConnectionError(f"Failed to establish RabbitMQ connection: {e}")

    async def open_channel(self, sniff_id: UUID):
        if not self._connection or self._connection.is_closed:
            raise ConnectionError("RabbitMQ connection is closed")

        async with asyncio.Lock():
            try:
                channel = self._connection.channel()
                with self.channels_lock:
                    self.channels[sniff_id] = channel
                return channel
            except Exception as e:
                raise RuntimeError(f"Failed to open channel: {e}")

    async def close_channel(self, sniff_id: UUID):
        async with asyncio.Lock():
            with self.channels_lock:
                channel = self.channels.pop(sniff_id)
                if channel:
                    try:
                        channel.close()
                    except Exception as e:
                        raise RuntimeError(f"Error while closing channel: {e}")
                else:
                    raise KeyError(f"Channel for {sniff_id} not found")

    async def close_connection(self):
        if self._connection:
            if not self._connection.is_closed:
                try:
                    self._connection.close()
                except Exception as e:
                    raise RuntimeError(f"Error while closing connection: {e}")
            else:
                print("Connection is already closed")
        else:
            raise ConnectionError("No active connection to close")
