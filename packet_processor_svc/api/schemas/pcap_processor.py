from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from typing import Dict, List
from scapy.all import Packet


class FileProcessStatus(str, Enum):
    Running = "Started"
    Processed = "Processed"
    Crashed = "Crashed"


class TCPFlags(int, Enum):
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    ACK = 0x10


class UploadStatus(BaseModel):
    status: FileProcessStatus
    upload_id: UUID


# class UploadStats(BaseModel):
#     tcp_sessions: int
#     udp_sessions: int


# class StreamSummary(BaseModel):
#     tcp_streams: Dict[str, List[bytes]]
#     udp_streams: Dict[str, List[bytes]]
#
#     @classmethod
#     def from_packets(cls, tcp_streams: Dict[str, List[Packet]], udp_streams: Dict[str, List[Packet]]):
#         return cls(
#             tcp_streams={k: [bytes(pkt) for pkt in v] for k, v in tcp_streams.items()},
#             udp_streams={k: [bytes(pkt) for pkt in v] for k, v in udp_streams.items()},
#         )
#
#     def to_packets(self):
#         return {
#             "tcp_streams": {k: [Packet(pkt) for pkt in v] for k, v in self.tcp_streams.items()},
#             "udp_streams": {k: [Packet(pkt) for pkt in v] for k, v in self.udp_streams.items()},
#         }
