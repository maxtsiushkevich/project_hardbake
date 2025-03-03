from scapy.all import AsyncSniffer
import asyncio

from api.core.tasks import tasks


def packet_summary(packet):
    summary = packet.summary()
    print(summary)


async def sniff_task(task_id: str, iface: str):
    sniffer = AsyncSniffer(iface=iface, prn=packet_summary)
    sniffer.start()
    tasks[task_id] = sniffer


def run_async_sniffer(task_id: str, iface: str):
    task = asyncio.create_task(sniff_task(task_id, iface))
    tasks[task_id] = task


def stop_async_sniffer(task_id: str) -> bool:
    sniffer = tasks.get(task_id)
    if sniffer:
        sniffer.stop()
        del tasks[task_id]
        return True
    else:
        return False
