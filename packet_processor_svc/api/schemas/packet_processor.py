from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from typing import Dict, List
from scapy.all import Packet


class FileProcessStatus(str, Enum):
    Running = "Started"
    Stopped = "Processed"
    Crashed = "Crashed"


@dataclass
class StreamSummary:
    tcp_streams: Dict[str, List[Packet]]
    udp_streams: Dict[str, List[Packet]]


class UploadResult(BaseModel):
    status: FileProcessStatus
    upload_id: UUID


class TCPFlags(int, Enum):
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    ACK = 0x10
