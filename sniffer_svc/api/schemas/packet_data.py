import time
from dataclasses import dataclass

from scapy.packet import Packet


@dataclass
class PacketData:
    packet: Packet
    timestamp: int = time.time_ns()