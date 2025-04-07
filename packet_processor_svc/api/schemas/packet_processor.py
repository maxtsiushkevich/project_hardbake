from dataclasses import dataclass
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


@dataclass
class StreamSummary:
    tcp_streams: Dict[str, List[Packet]]
    udp_streams: Dict[str, List[Packet]]


@dataclass
class PcapProcessResult:
    info: UploadStatus
    tcp_streams: Dict[str, List[Packet]]
    udp_streams: Dict[str, List[Packet]]
