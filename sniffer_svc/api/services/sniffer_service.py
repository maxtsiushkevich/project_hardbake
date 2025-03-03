from scapy.all import AsyncSniffer
import asyncio

from api.core.context import tasks, sniffers


def packet_summary(packet):
    summary = packet.summary()
    print(summary)


async def sniff_task(task_id: str, iface: str):
    sniffer = AsyncSniffer(iface=iface, prn=packet_summary)
    sniffer.start()
    sniffers[task_id] = sniffer


async def run_async_sniffer(task_id: str, iface: str):
    task = asyncio.create_task(sniff_task(task_id, iface))
    tasks[task_id] = task


async def stop_async_sniffer(task_id: str) -> bool:
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


async def get_task_ids() -> list[str]:
    return list(tasks.keys())