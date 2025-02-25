import enum
from datetime import datetime

from pydantic import BaseModel

import uuid


class Status(enum.Enum):
    Started = 1
    Stopped = 2
    Error = 3


class Session(BaseModel):
    id: uuid.UUID
    interface: str
    start: datetime
    stop: datetime
    duration: datetime
    status: Status
