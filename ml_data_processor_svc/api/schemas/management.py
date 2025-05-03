from pydantic import BaseModel
from enum import Enum
from typing import Optional


class ConsumerStatusEnum(str, Enum):
    NOT_RUNNING = "Not running"
    RUNNING = "Running"
    STOPPED = "Stopped"
    ERROR = "Error"


class StartStopResponse(BaseModel):
    status: ConsumerStatusEnum


class ConsumerStatusResponse(BaseModel):
    status: ConsumerStatusEnum
    error: Optional[str] = None
