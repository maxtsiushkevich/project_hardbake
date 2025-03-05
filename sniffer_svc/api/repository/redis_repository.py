import os
from contextlib import redirect_stderr, redirect_stdout

import redis.asyncio as redis
from uuid import UUID

from api.schemas.sniffer import SniffDetails, StartSniffDetails, SniffStatus
from datetime import datetime


def get_redis_connection():
    host = os.getenv("REDIS_HOST")
    port = os.getenv("REDIS_PORT")
    return redis.Redis(host=host, port=int(port), db=0)


class RedisConnection:
    def __init__(self):
        host = os.getenv("REDIS_HOST")
        port = os.getenv("REDIS_PORT")
        self.redis = redis.Redis(host=host, port=int(port), db=0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.redis.close()


class RedisRepository:
    def __init__(self, conn):
        self.connection = conn

    async def save_sniff(self, details: StartSniffDetails):
        data = SniffDetails(
            interface=details.interface,
            sniff_id=details.sniff_id,
            start_at=details.start_at,
            status=SniffStatus.Running,
        )
        await self.connection.set(str(details.sniff_id), data.model_dump_json())

    async def update_sniff(self, sniff_id: UUID, new_status: SniffStatus):
        sniff_details = await get_sniff(sniff_id)
        if not sniff_details:
            raise ValueError(f"Sniff details for ID {sniff_id} not found.")
        sniff_details.status = new_status
        await self.connection.set(str(sniff_id), sniff_details.model_dump_json())

    async def stop_sniff(self, sniff_id: UUID):
        sniff_details = await get_sniff(sniff_id)
        if not sniff_details:
            raise ValueError(f"No sniff with {sniff_id}.")

        sniff_details.status = SniffStatus.Stopped
        sniff_details.stop_at = datetime.now()
        await self.connection.set(str(sniff_id), sniff_details.model_dump_json())

    def get_sniff(self):
        pass


redis_conn = get_redis_connection()


async def get_sniff(sniff_id: UUID) -> SniffDetails | None:
    data = await redis_conn.get(str(sniff_id))
    if data:
        return SniffDetails.model_validate_json(data)
    return None


async def update_sniff_status(sniff_id: UUID, new_status: SniffStatus):
    sniff_details = await get_sniff(sniff_id)
    if not sniff_details:
        raise ValueError(f"Sniff details for ID {sniff_id} not found.")

    sniff_details.status = new_status
    await redis_conn.set(str(sniff_id), sniff_details.model_dump_json())


async def get_all_sniffs_redis(start_pos: int | None = None, quantity: int | None = None) -> list[SniffDetails]:
    keys = await redis_conn.keys("*")

    if start_pos is not None and quantity is not None:
        keys = keys[start_pos:start_pos + quantity]
    elif start_pos is not None:
        keys = keys[start_pos:]
    elif quantity is not None:
        keys = keys[:quantity]

    sniffs = []
    for key in keys:
        data = await redis_conn.get(key)
        if data:
            sniffs.append(SniffDetails.model_validate_json(data))

    return sniffs
