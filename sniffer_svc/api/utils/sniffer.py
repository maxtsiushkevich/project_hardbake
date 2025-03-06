from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer

from api.core.context import sniffers
from api.repository.redis_repository import RedisRepository
from api.schemas.sniffer import SniffStatus


def packet_summary(packet):
    summary = packet.summary()
    print(summary)


async def sniff_task(task_id: UUID, iface: str, redis: RedisRepository):
    try:
        sniffer = AsyncSniffer(iface=iface, prn=packet_summary)
        sniffer.start()
        sniffers[task_id] = sniffer
    except Exception as e:
        await redis.update_sniff_status(task_id, SniffStatus.Crashed)
        raise
