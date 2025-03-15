from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class SniffStatus(str, Enum):
    Running = "Running"
    Stopped = "Stopped"
    Crashed = "Crashed"


class StartSniffDetails(BaseModel):
    interface: str = Field(..., description="Network interface being sniffed")
    sniff_id: UUID = Field(..., description="Unique ID of the sniffing session")
    start_at: datetime = Field(..., description="Timestamp when sniffing started")


class SniffDetails(BaseModel):
    interface: str = Field(..., description="Network interface being sniffed")
    sniff_id: UUID = Field(..., description="Unique ID of the sniffing session")
    start_at: datetime = Field(..., description="Timestamp when sniffing started")
    stop_at: Optional[datetime] = Field(None, description="Timestamp when sniffing stopped")
    status: SniffStatus = Field(SniffStatus.Running, description="Current status of sniffing session")

    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }


class SniffListResponse(BaseModel):
    sniffs: List[SniffDetails] = Field(..., description="List of sniffing sessions")
    total: int = Field(..., description="Total number of sniffing sessions")


class SniffFilter(BaseModel):
    src_ip: Optional[str] = Field(None)
    dst_ip: Optional[str] = Field(None)
    protocol: Optional[str] = Field(None)
    src_port: Optional[int] = Field(None)
    dst_port: Optional[int] = Field(None)

    def to_bpf(self) -> str:
        filters = []

        if self.src_ip:
            filters.append(f"src host {self.src_ip}")
        if self.dst_ip:
            filters.append(f"dst host {self.dst_ip}")
        if self.protocol:
            filters.append(self.protocol)
        if self.src_port:
            filters.append(f"src port {self.src_port}")
        if self.dst_port:
            filters.append(f"dst port {self.dst_port}")

        return " and ".join(filters) if filters else ""
