from pydantic import BaseModel
from enum import Enum
from typing import Optional


class DetectionStatusEnum(str, Enum):
    NOT_RUNNING = "Not running"
    RUNNING = "Running"
    STOPPED = "Stopped"
    ERROR = "Error"


class StartStopResponse(BaseModel):
    status: DetectionStatusEnum


class DetectionStatusResponse(BaseModel):
    status: DetectionStatusEnum
    error: Optional[str] = None


class BatchSizeResponse(BaseModel):
    size: int


class UploadStatus(str, Enum):
    UPLOADED = 'Uploaded'
    ERROR = 'Error'


class UploadStatusResponse(BaseModel):
    status: UploadStatus
