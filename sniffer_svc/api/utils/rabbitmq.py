import asyncio
import os
import threading
from uuid import UUID

import pika
from dotenv import load_dotenv
from pika.adapters.asyncio_connection import AsyncioConnection

from api.exceptions.exceptions import RabbitMQError


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
                raise RabbitMQError("Missing RabbitMQ configuration in environment variables")

            self._credentials = pika.PlainCredentials(user, password)
            self._connection_params = pika.ConnectionParameters(
                host=host,
                port=int(port),
                credentials=self._credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            self._connection = None
            self._connect_event = asyncio.Event()
            self._connection_lock = asyncio.Lock()
            self.channels = {}
            self.channels_lock = threading.Lock()

    async def ensure_connection(self):
        """Ensure we have an active connection"""
        async with self._connection_lock:
            if self._connection and not self._connection.is_closed:
                return

            self._connect_event.clear()
            self._connect()

            try:
                await asyncio.wait_for(self._connect_event.wait(), timeout=5)
            except asyncio.TimeoutError:
                raise RabbitMQError("Failed to establish RabbitMQ connection: timeout")

            if not self._connection or self._connection.is_closed:
                raise RabbitMQError("RabbitMQ connection is not available")

    def _connect(self):
        if self._connection and not self._connection.is_closed:
            return

        try:
            self._connection = AsyncioConnection(
                self._connection_params,
                on_open_callback=self._on_connection_open,
                on_open_error_callback=self._on_connection_open_error,
                on_close_callback=self._on_connection_closed
            )
        except Exception as e:
            self._connect_event.set()
            raise RabbitMQError(f"Failed to establish RabbitMQ connection: {e}")

    def _on_connection_open(self, _unused_connection):
        print("RabbitMQ connection established")
        self._connect_event.set()

    def _on_connection_open_error(self, _unused_connection, err):
        print(f"RabbitMQ connection open failed: {err}")
        self._connect_event.set()
        raise RabbitMQError(f"Connection open error: {err}")

    def _on_connection_closed(self, _unused_connection, reason):
        print(f"RabbitMQ connection closed: {reason}")
        self._connect_event.clear()
        with self.channels_lock:
            self.channels.clear()

    async def open_channel(self, sniff_id: UUID):
        """Open a dedicated channel for specific sniff_id"""
        await self.ensure_connection()

        async with asyncio.Lock():
            try:
                with self.channels_lock:
                    if sniff_id in self.channels:
                        channel = self.channels[sniff_id]
                        if channel and not channel.is_closed:
                            return channel

                channel = await asyncio.get_running_loop().run_in_executor(
                    None,
                    self._connection.channel
                )

                if not channel or channel.is_closed:
                    raise RabbitMQError("Failed to create channel")

                with self.channels_lock:
                    self.channels[sniff_id] = channel

                return channel
            except Exception as e:
                raise RabbitMQError(f"Failed to open channel: {e}")

    async def close_channel(self, sniff_id: UUID):
        """Close channel for specific sniff_id"""
        async with asyncio.Lock():
            with self.channels_lock:
                channel = self.channels.pop(sniff_id, None)
                if channel:
                    try:
                        await asyncio.get_running_loop().run_in_executor(
                            None,
                            channel.close
                        )
                    except Exception as e:
                        raise RabbitMQError(f"Error while closing channel: {e}")
                else:
                    raise RabbitMQError(f"Channel for {sniff_id} not found")

    async def close_connection(self):
        """Close connection and all channels"""
        if self._connection:
            if not self._connection.is_closed:
                try:
                    with self.channels_lock:
                        for channel in self.channels.values():
                            try:
                                channel.close()
                            except Exception:
                                pass
                        self.channels.clear()

                    await asyncio.get_running_loop().run_in_executor(
                        None,
                        self._connection.close
                    )
                except Exception as e:
                    raise RabbitMQError(f"Error while closing connection: {e}")
            else:
                print("Connection is already closed")
        else:
            raise RabbitMQError("No active connection to close")
