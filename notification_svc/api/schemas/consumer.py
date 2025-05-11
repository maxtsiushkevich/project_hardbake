from pydantic import BaseModel
from enum import Enum
from typing import Optional


class ConsumingStatusEnum(str, Enum):
    NOT_RUNNING = "Not running"
    RUNNING = "Running"
    STOPPED = "Stopped"
    ERROR = "Error"

class ConsumingsStatusResponse(BaseModel):
    status: ConsumingStatusEnum
    error: Optional[str] = None

class StartStopResponse(BaseModel):
    status: ConsumingStatusEnum