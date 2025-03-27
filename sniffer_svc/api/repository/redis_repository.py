import os
import pickle

import redis.asyncio as redis
from uuid import UUID

from api.schemas.sniffer import SniffDetails, StartSniffDetails, SniffStatus
from datetime import datetime


class RedisConnection:
    def __init__(self):
        host = os.getenv("REDIS_HOST")
        port = os.getenv("REDIS_PORT")
        self.redis = redis.Redis(host=host, port=int(port), db=0)

    @property
    def connection(self):
        return self.redis

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
        await self.connection.set(str(details.sniff_id), pickle.dumps(data))

    async def update_sniff(self, sniff_id: UUID, new_status: SniffStatus):
        sniff_details = await self.get_sniff(sniff_id)
        if not sniff_details:
            raise ValueError(f"Sniff details for ID {sniff_id} not found.")
        sniff_details.status = new_status
        await self.connection.set(str(sniff_id), pickle.dumps(sniff_details))

    async def stop_sniff(self, sniff_id: UUID):
        sniff_details = await self.get_sniff(sniff_id)
        if not sniff_details:
            raise ValueError(f"No sniff with {sniff_id}.")

        sniff_details.status = SniffStatus.Stopped
        sniff_details.stop_at = datetime.now()
        await self.connection.set(str(sniff_id), pickle.dumps(sniff_details))
        return sniff_details

    async def get_sniff(self, sniff_id: UUID) -> SniffDetails | None:
        data = await self.connection.get(str(sniff_id))
        if data:
            return pickle.loads(data)
        return None

    async def get_by_status(self, status: SniffStatus):
        keys = await self.connection.keys("*")
        active_sniffs = []

        for key in keys:
            data = await self.connection.get(key)
            if data:
                sniff_details = pickle.loads(data)
                if sniff_details.status == status:
                    active_sniffs.append(sniff_details)

        return active_sniffs

    async def is_sniffer_running(self, iface: str) -> bool:
        keys = await self.connection.keys("*")
        for key in keys:
            data = await self.connection.get(key)
            sniff_details = pickle.loads(data)
            if data:
                if sniff_details.interface == iface and sniff_details.status == SniffStatus.Running:
                    return True
        return False

    async def get_all(self, start_pos: int | None = None, quantity: int | None = None) -> list[SniffDetails]:
        keys = await self.connection.keys("*")

        if start_pos is not None and quantity is not None:
            keys = keys[start_pos:start_pos + quantity]
        elif start_pos is not None:
            keys = keys[start_pos:]
        elif quantity is not None:
            keys = keys[:quantity]

        sniffs = []
        for key in keys:
            data = await self.connection.get(key)
            if data:
                sniffs.append(pickle.loads(data))

        return sniffs
