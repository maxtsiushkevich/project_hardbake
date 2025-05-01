import time
import struct
from dataclasses import dataclass, field

from scapy.compat import raw
from scapy.layers.l2 import Ether
from scapy.packet import Packet

from api.core.logger import logger


@dataclass
class PacketData:
    packet: Packet
    timestamp: int = field(default_factory=time.time_ns)

    def to_bytes(self) -> bytes:
        """Serialize PacketData to bytes.

        Format:
        - 8 bytes: timestamp (nanoseconds, big-endian)
        - 4 bytes: packet length (big-endian)
        - N bytes: packet data
        """
        logger.debug(f"Serializing packet with timestamp {self.timestamp}")
        try:
            packet_bytes = raw(self.packet)
            timestamp_bytes = struct.pack('>Q', self.timestamp)
            length_bytes = struct.pack('>I', len(packet_bytes))
            serialized = timestamp_bytes + length_bytes + packet_bytes
            logger.debug(f"Serialized packet: timestamp={self.timestamp}, length={len(packet_bytes)}")
            return serialized
        except Exception as e:
            logger.error(f"Error serializing packet: {e}", exc_info=True)
            raise

    @staticmethod
    def from_bytes(byte_packetdata: bytes) -> 'PacketData':
        """Deserialize bytes back to PacketData.

        Args:
            byte_packetdata: Bytes in the format produced by to_bytes()

        Returns:
            Reconstructed PacketData object
        """
        logger.debug(f"Deserializing packet data of length {len(byte_packetdata)}")
        try:
            timestamp = struct.unpack('>Q', byte_packetdata[:8])[0]
            pkt_length = struct.unpack('>I', byte_packetdata[8:12])[0]
            packet_bytes = byte_packetdata[12:12 + pkt_length]

            packet = Ether(packet_bytes)
            logger.debug(f"Deserialized packet: timestamp={timestamp}, length={pkt_length}")
            return PacketData(packet=packet, timestamp=timestamp)
        except Exception as e:
            logger.error(f"Error deserializing packet: {e}", exc_info=True)
            raise
