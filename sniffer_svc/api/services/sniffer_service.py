from uuid import UUID, uuid4

import asyncio

from api.core.context import tasks, sniffers
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
            task = asyncio.create_task(sniff_task(sniff_id, iface, self.redis))
            tasks[sniff_id] = task
            details = StartSniffDetails(sniff_id=sniff_id, start_at=datetime.now(), interface=iface)
            await self.redis.save_sniff(details)
            return details
        except Exception as e:
            await self.redis.update_sniff(sniff_id, SniffStatus.Crashed)

    async def stop(self, task_id: UUID):
        sniffer = sniffers.get(task_id)
        task = tasks.get(task_id)

        if not sniffer or not task:
            raise SniffNotFoundError(f"Sniffer {task_id} not found")

        if sniffer:
            sniffer.stop()
            del sniffers[task_id]
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del tasks[task_id]

        result = await self.redis.stop_sniff(task_id)
        return result

    async def get_active(self):
        result = await self.redis.get_active()
        return result

    async def get_all(self, start_pos: int | None = None, quantity: int | None = None):
        sniffs = await self.redis.get_all(start_pos, quantity)
        return sniffs

    async def get(self, sniff_id: UUID):
        result = await self.redis.get_sniff(sniff_id)
        return result
