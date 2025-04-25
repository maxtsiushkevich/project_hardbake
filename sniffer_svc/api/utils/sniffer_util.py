import os
import pickle

import pika
from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer
from scapy.utils import PcapNgWriter

from api.core.context import sniffers, rabbitmq_client
from api.exceptions.exceptions import RabbitMQError, SniffNotFoundError
from api.schemas.packet_data import PacketData


class SnifferUtil:
    def __init__(self):
        self.is_crashed: bool = False

    def packet_operator(self, packet, channel, writer=None):
        try:
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

        except Exception as e:
            print(f"{e}")
            self.is_crashed = True
            print("packet_operator")
            # raise e

    def _is_crashed(self, pkt):
        return not self.is_crashed

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
                filter=filters,
                lfilter=self._is_crashed
            )

            sniffer.start()
            sniffers[sniff_id] = sniffer

        except RabbitMQError as e:
            print("start_sniffing")
            raise e

    async def stop_sniffing(self, sniff_id: UUID):
        sniffer = sniffers.get(sniff_id)

        if not sniffer:
            raise SniffNotFoundError(f"Sniffer {sniff_id} not found")
        try:
            await rabbitmq_client.close_channel(sniff_id)
        except Exception as e:
            pass
        if sniffer.running:
            sniffer.stop()
        del sniffers[sniff_id]
