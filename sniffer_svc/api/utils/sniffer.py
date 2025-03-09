from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer

from api.core.context import sniffers
from api.repository.redis_repository import RedisRepository
from api.schemas.sniffer import SniffStatus


def packet_summary(packet):
    summary = packet.summary()
    print(summary)


async def sniff_task(sniff_id: UUID, iface: str, redis: RedisRepository):
    try:
        sniffer = AsyncSniffer(iface=iface, prn=packet_summary)
        sniffer.start()
        sniffers[sniff_id] = sniffer
    except Exception as e:
        await redis.update_sniff_status(sniff_id, SniffStatus.Crashed)
        raise
