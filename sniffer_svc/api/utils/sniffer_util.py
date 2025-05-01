import os
import pickle

import pika
from scapy.layers.msrpce.raw.ms_drsr import UUID
from scapy.sendrecv import AsyncSniffer
from scapy.utils import PcapNgWriter

from api.core.context import sniffers, rabbitmq_client
from api.core.logger import logger
from api.exceptions.exceptions import RabbitMQError, SniffNotFoundError
from api.schemas.packet_data import PacketData


class SnifferUtil:
    def __init__(self):
        self.is_crashed: bool = False

    def packet_operator(self, packet, channel, writer=None):
        try:
            if writer:
                writer.write(packet)
                logger.debug("Packet written to pcap file")

            packet_data = PacketData(packet)
            logger.debug(f"Captured packet: {packet.summary()}")
            packet_data = packet_data.to_bytes()
            data = pickle.dumps(packet_data)

            channel.basic_publish(
                exchange='sniffer_svc.raw_packets.fanout',
                routing_key='',
                body=data,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            logger.debug("Packet published to RabbitMQ")
        except Exception as e:
            self.is_crashed = True
            logger.error(f"Error in packet_operator: {e}", exc_info=True)
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
                file_path = os.path.join(pcap_dir, f"{iface}_{sniff_id}.pcapng")
                writer = PcapNgWriter(file_path)
                logger.info(f"Writing packets to file: {file_path}")

            sniffer = AsyncSniffer(
                iface=iface,
                prn=lambda pkt: self.packet_operator(pkt, channel, writer),
                filter=filters,
                lfilter=self._is_crashed
            )

            sniffer.start()
            sniffers[sniff_id] = sniffer
            logger.info(f"Sniffer started and registered in context with sniff_id={sniff_id}")

        except RabbitMQError as e:
            logger.error(f"RabbitMQ error during start_sniffing for sniff_id={sniff_id}: {e}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during start_sniffing: {e}", exc_info=True)
            raise

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
        logger.debug(f"Sniffer removed from context for sniff_id={sniff_id}")
