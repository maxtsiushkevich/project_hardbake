from uuid import UUID, uuid4

from fastapi import FastAPI
from scapy.all import AsyncSniffer
import asyncio

from api.core.context import tasks, sniffers
from api.exceptions.exceptions import SniffNotFoundError
from api.schemas.sniffer import SniffStatus, StartSniffDetails
from api.repository.redis_repository import update_sniff_status, RedisRepository
from datetime import datetime


class SnifferService:

    def __init__(self, redis: RedisRepository):
        self.redis = redis

    async def start(self, iface: str):
        sniff_id = uuid4()
        try:
            task = asyncio.create_task(sniff_task(sniff_id, iface))
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

        await self.redis.stop_sniff(task_id)

    async def get_active_sniffs(self) -> list[UUID]:
        # делать запрос в редис с выборкой сниффов со статусом Running
        return list(tasks.keys())


def packet_summary(packet):
    summary = packet.summary()
    print(summary)


async def sniff_task(task_id: UUID, iface: str):
    try:
        sniffer = AsyncSniffer(iface=iface, prn=packet_summary)
        sniffer.start()
        sniffers[task_id] = sniffer
    except Exception as e:
        await update_sniff_status(task_id, SniffStatus.Crashed)
        raise
