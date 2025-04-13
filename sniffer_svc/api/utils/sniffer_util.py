import os
import pickle

import pika
from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer
from scapy.utils import PcapNgWriter

from api.core.context import sniffers, rabbitmq_client
from api.repository.redis_repository import RedisRepository
from api.schemas.packet_data import PacketData
from api.schemas.sniffer import SniffStatus


class SnifferUtil:
    def __init__(self, redis_repo: RedisRepository):
        self.redis = redis_repo

    def packet_operator(self, packet, channel, writer=None):
        if writer:
            writer.write(packet)

        packet_data = PacketData(packet)

        print(packet.summary())
        packet_data = packet_data.to_bytes()
        data = pickle.dumps(packet_data)

        channel.basic_publish(
            exchange='sniffer_svc.raw_packets.fanout',
            routing_key='',
            body=data,
            properties=pika.BasicProperties(delivery_mode=2)
        )

    async def start_sniffing(self, sniff_id: UUID, iface: str, filters: str | None = None, write_in_file: bool = False):
        try:
            channel = await rabbitmq_client.open_channel(sniff_id)

            writer = None
            if write_in_file:
                pcap_dir = "pcap"
                os.makedirs(pcap_dir, exist_ok=True)
                writer = PcapNgWriter(os.path.join(pcap_dir, f"{iface}_{sniff_id}.pcapng"))

            sniffer = AsyncSniffer(
                iface=iface,
                prn=lambda pkt: self.packet_operator(pkt, channel, writer),
                filter=filters
            )

            sniffer.start()
            sniffers[sniff_id] = sniffer

        except Exception as e:
            await self.redis.update_sniff(sniff_id, SniffStatus.Crashed)
            raise e
