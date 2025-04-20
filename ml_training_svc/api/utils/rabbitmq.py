import asyncio
import os
import threading
from dotenv import load_dotenv
import pika
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
                heartbeat=600,
                blocked_connection_timeout=300
            )

            self._connection = None
            self._channel = None
            self._connect_event = asyncio.Event()

    def _connect(self):
        try:
            self._connection = AsyncioConnection(
                self._connection_params,
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_open_error,
                on_close_callback=self._on_connection_closed
            )
        except Exception as e:
            raise ConnectionError(f"Failed to establish RabbitMQ connection: {e}")

    def _on_connection_open(self, connection):
        print("RabbitMQ connection established")
        connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        print("RabbitMQ channel opened")
        self._channel = channel
        self._connect_event.set()

    def _on_connection_open_error(self, _unused_connection, err):
        print(f"RabbitMQ connection open failed: {err}")
        self._connect_event.set()
        raise ConnectionError(f"Connection open error: {err}")

    def _on_connection_closed(self, _unused_connection, reason):
        print(f"RabbitMQ connection closed: {reason}")
        self._connect_event.clear()
        self._channel = None

    async def get_channel(self):
        if not self._connection or self._connection.is_closed:
            self._connect()

        await self._connect_event.wait()

        if not self._channel or self._channel.is_closed:
            raise ConnectionError("RabbitMQ channel is not available")

        return self._channel

    async def close(self):
        if self._connection:
            await asyncio.get_running_loop().run_in_executor(None, self._connection.close)

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

    async def create_channel(self):
        """Create new channel for producer. Requires manual closing"""
        if not self._connection or self._connection.is_closed:
            self._connect()
        await self._connect_event.wait()

        channel = await asyncio.get_running_loop().run_in_executor(None, self._connection.channel)

        if not channel or channel.is_closed:
            raise ConnectionError("Failed to create channel")

        return channel
