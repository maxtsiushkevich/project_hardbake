import pika
from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer

from api.core.context import sniffers, rabbitmq_client
from api.repository.redis_repository import RedisRepository
from api.schemas.sniffer import SniffStatus


def packet_operator(packet, channel=None):
    raw_packet = bytes(packet)
    channel.basic_publish(
                        exchange='sniffer_svc.raw_packets.fanout',
                        routing_key='',
                        body=raw_packet,
                        properties=pika.BasicProperties(delivery_mode=2)
                    )


async def sniff_task(sniff_id: UUID, iface: str, filters: str | None, redis: RedisRepository):
    try:
        channel = await rabbitmq_client.open_channel(sniff_id)
        sniffer = AsyncSniffer(iface=iface, prn=lambda pkt: packet_operator(pkt, channel), filter=filters)
        sniffer.start()
        sniffers[sniff_id] = sniffer
    except Exception as e:
        await redis.update_sniff(sniff_id, SniffStatus.Crashed)
        raise
