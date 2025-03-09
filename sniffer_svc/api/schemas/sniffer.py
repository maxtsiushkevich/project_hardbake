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
