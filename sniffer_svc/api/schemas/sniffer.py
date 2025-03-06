from enum import Enum
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class SniffStatus(Enum):
    Running = "Running"
    Stopped = "Stopped"
    Crashed = "Crashed"


class StartSniffDetails(BaseModel):
    interface: str
    sniff_id: UUID
    start_at: datetime


class StopSniffDetails(BaseModel):
    sniff_id: UUID
    stop_at: datetime


class SniffDetails(BaseModel):
    interface: str
    sniff_id: UUID
    start_at: datetime
    stop_at: Optional[datetime] = None
    status: SniffStatus = SniffStatus.Running

    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }
