from uuid import UUID

from scapy.all import AsyncSniffer
import asyncio

from api.core.context import tasks, sniffers
from api.schemas.sniffer import SniffStatus
from api.services.redis_service import update_sniff_status


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

async def run_async_sniffer(task_id: UUID, iface: str):
    try:
        task = asyncio.create_task(sniff_task(task_id, iface))
        tasks[task_id] = task
    except Exception as e:
        await update_sniff_status(task_id, SniffStatus.Crashed)


async def stop_async_sniffer(task_id: UUID) -> bool:
    sniffer = sniffers.get(task_id)
    task = tasks.get(task_id)
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
        return True
    return False


async def get_task_ids() -> list[UUID]:
    return list(tasks.keys())