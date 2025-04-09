import base64
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from typing import Dict, List
from scapy.all import Packet
from scapy.compat import raw


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


class StreamSummary(BaseModel):
    tcp_streams: Dict[str, List[str]]
    udp_streams: Dict[str, List[str]]

    @classmethod
    def from_packets(cls, tcp_streams: Dict[str, List[Packet]], udp_streams: Dict[str, List[Packet]]):
        return cls(
            tcp_streams={k: [base64.b64encode(raw(pkt)).decode('utf-8') for pkt in v] for k, v in tcp_streams.items()},
            udp_streams={k: [base64.b64encode(raw(pkt)).decode('utf-8') for pkt in v] for k, v in udp_streams.items()},
        )

    def to_packets(self):
        return {
            "tcp_streams": {k: [Packet(base64.b64decode(pkt)) for pkt in v] for k, v in self.tcp_streams.items()},
            "udp_streams": {k: [Packet(base64.b64decode(pkt)) for pkt in v] for k, v in self.udp_streams.items()},
        }