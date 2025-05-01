import logging
from scapy.all import Packet
from scapy.layers.inet import IP, TCP, UDP
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class StreamKeyExtractor:
    def __init__(self, packet: Packet):
        self.packet = packet

    @property
    def stream_key(self):
        if not self.packet.haslayer(IP):
            logger.debug(f"Packet {self.packet} doesnt contain IP layer")
            return None, None

        src_ip = self.packet[IP].src
        dst_ip = self.packet[IP].dst

        if self.packet.haslayer(TCP):
            src_port = self.packet[TCP].sport
            dst_port = self.packet[TCP].dport
            proto = "TCP"
        elif self.packet.haslayer(UDP):
            src_port = self.packet[UDP].sport
            dst_port = self.packet[UDP].dport
            proto = "UDP"
        else:
            logger.debug("Packet doesnt contain TCP or UDP layer.")
            return None, None

        key = f"{src_ip}-{dst_ip}-{src_port}-{dst_port}-{proto}"
        alt_key = f"{dst_ip}-{src_ip}-{dst_port}-{src_port}-{proto}"
        logger.debug(f"Generated stream keys: key={key}, alt_key={alt_key}")
        return key, alt_key
