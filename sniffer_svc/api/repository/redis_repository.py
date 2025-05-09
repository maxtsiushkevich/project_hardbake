import os
import pickle
import redis.asyncio as redis
from uuid import UUID

from api.core.logger import logger
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
        logger.info(f'Saved to Redis: {data}')

    async def update_sniff(self, sniff_id: UUID, new_status: SniffStatus):
        sniff_details = await self.get_sniff(sniff_id)
        if not sniff_details:
            logger.error(f"Failed to update: Sniff ID {sniff_id} not found.", exc_info=True)
            raise ValueError(f"Sniff details for ID {sniff_id} not found.")
        sniff_details.status = new_status
        await self.connection.set(str(sniff_id), pickle.dumps(sniff_details))
        logger.info(f"Updated sniff ID {sniff_id} to status {new_status}.")

    async def stop_sniff(self, sniff_id: UUID):
        sniff_details = await self.get_sniff(sniff_id)
        if not sniff_details:
            logger.error(f"Failed to stop: No sniff with ID {sniff_id}.", exc_info=True)
            raise ValueError(f"No sniff with {sniff_id}.")

        sniff_details.status = SniffStatus.Stopped
        sniff_details.stop_at = datetime.now()
        await self.connection.set(str(sniff_id), pickle.dumps(sniff_details))
        logger.info(f"Stopped sniff: {sniff_details}")
        return sniff_details

    async def get_sniff(self, sniff_id: UUID) -> SniffDetails | None:
        data = await self.connection.get(str(sniff_id))
        if data:
            sniff_details = pickle.loads(data)
            logger.debug(f"Fetched sniff ID {sniff_id}: {sniff_details}")
            return sniff_details
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

        logger.info(f"Found {len(active_sniffs)} sniffs with status {status}.")
        return active_sniffs

    async def is_sniffer_running(self, iface: str) -> bool:
        keys = await self.connection.keys("*")
        for key in keys:
            data = await self.connection.get(key)
            if data:
                sniff_details = pickle.loads(data)
                if sniff_details.interface == iface and sniff_details.status == SniffStatus.Running:
                    logger.info(f"Sniffer is already running on interface {iface}.")
                    return True
        logger.info(f"No running sniffer found on interface {iface}.")
        return False

    async def get_all(self, start_pos: int | None = None, quantity: int | None = None) -> list[SniffDetails]:
        keys = await self.connection.keys("*")

        total_keys = len(keys)
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

        logger.info(f"Fetched {len(sniffs)} sniffs out of {total_keys} total keys.")
        return sniffs

    async def clear_cache(self):
        try:
            keys = await self.connection.keys("*")
            removed_count = 0

            for key in keys:
                data = await self.connection.get(key)
                if data:
                    sniff_details = pickle.loads(data)
                    if sniff_details.status in {SniffStatus.Stopped, SniffStatus.Crashed}:
                        await self.connection.delete(key)
                        removed_count += 1
            logger.info(f"Cleared {removed_count} sniffs with status Stopped or Crashed.")
        except Exception as e:
            raise e
