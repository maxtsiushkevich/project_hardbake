from uuid import UUID, uuid4

import asyncio

from api.core.context import sniffers
from api.exceptions.exceptions import SniffNotFoundError
from api.schemas.sniffer import SniffStatus, StartSniffDetails
from api.repository.redis_repository import RedisRepository
from datetime import datetime

from api.utils.sniffer import sniff_task


class SnifferService:

    def __init__(self, redis: RedisRepository):
        self.redis = redis

    async def start(self, iface: str):
        sniff_id = uuid4()
        try:
            asyncio.create_task(sniff_task(sniff_id, iface, self.redis))
            details = StartSniffDetails(sniff_id=sniff_id, start_at=datetime.now(), interface=iface)
            await self.redis.save_sniff(details)
            return details
        except Exception as e:
            await self.redis.update_sniff(sniff_id, SniffStatus.Crashed)

    async def stop(self, sniff_id: UUID):
        sniffer = sniffers.get(sniff_id)

        if not sniffer:
            raise SniffNotFoundError(f"Sniffer {sniff_id} not found")

        if sniffer:
            sniffer.stop()
            del sniffers[sniff_id]

        result = await self.redis.stop_sniff(sniff_id)
        return result

    async def get_by_status(self, status: SniffStatus):
        result = await self.redis.get_by_status(status)
        return result

    async def get_all(self, start_pos: int | None = None, quantity: int | None = None):
        sniffs = await self.redis.get_all(start_pos, quantity)
        return sniffs

    async def get(self, sniff_id: UUID):
        result = await self.redis.get_sniff(sniff_id)
        return result
