import asyncio
import os
import threading
from dotenv import load_dotenv
import pika
from pika.adapters.asyncio_connection import AsyncioConnection

from api.core.logger import logger


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
                logger.error("Missing RabbitMQ configuration in environment variables", exc_info=True)
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
            logger.info("RabbitMQClient initialized")

    def _connect(self):
        logger.info("Attempting to connect to RabbitMQ")
        try:
            self._connection = AsyncioConnection(
                self._connection_params,
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_open_error,
                on_close_callback=self._on_connection_closed
            )
        except Exception as e:
            logger.error("Exception during RabbitMQ _connect()", exc_info=True)
            raise ConnectionError(f"Failed to establish RabbitMQ connection: {e}")

    def _on_connection_open(self, connection):
        logger.info("RabbitMQ connection established")
        connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        logger.info("RabbitMQ channel successfully opened")
        self._channel = channel
        self._connect_event.set()

    def _on_connection_open_error(self, _unused_connection, err):
        logger.error(f"RabbitMQ connection open failed: {err}", exc_info=True)
        self._connect_event.set()
        # raise ConnectionError(f"Connection open error: {err}")

    def _on_connection_closed(self, _unused_connection, reason):
        logger.warning(f"RabbitMQ connection closed: {reason}")
        self._connect_event.clear()
        self._channel = None

    async def get_channel(self):
        if not self._connection or self._connection.is_closed:
            logger.info("RabbitMQ connection is not open, reconnecting")
            self._connect()

        await self._connect_event.wait()

        if not self._channel or self._channel.is_closed:
            logger.warning("RabbitMQ channel is not available or closed")
            raise ConnectionError("RabbitMQ channel is not available")

        logger.info("Returning RabbitMQ channel")
        return self._channel

    async def close(self):
        if self._connection:
            logger.info("Closing RabbitMQ connection")
            await asyncio.get_running_loop().run_in_executor(None, self._connection.close)

    async def close_connection(self):
        if self._connection:
            if not self._connection.is_closed:
                try:
                    logger.info("Closing RabbitMQ connection")
                    self._connection.close()
                except Exception as e:
                    logger.error("Error while closing RabbitMQ connection", exc_info=True)
                    raise RuntimeError(f"Error while closing connection: {e}")
            else:
                logger.info("RabbitMQ connection already closed")
        else:
            logger.warning("No active RabbitMQ connection to close")
            raise ConnectionError("No active connection to close")

    async def create_channel(self):
        """Create new channel for producer. Requires manual closing"""
        logger.info("Creating new RabbitMQ channel")
        if not self._connection or self._connection.is_closed:
            self._connect()
        await self._connect_event.wait()

        channel = await asyncio.get_running_loop().run_in_executor(None, self._connection.channel)

        if not channel or channel.is_closed:
            logger.error("Failed to create RabbitMQ channel")
            raise ConnectionError("Failed to create channel")

        logger.info("New RabbitMQ channel created")
        return channel
