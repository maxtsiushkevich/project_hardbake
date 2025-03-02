import uuid
from datetime import datetime

from pydantic import BaseModel



class StartSniffDetails(BaseModel):
    interface: str
    sniff_id: uuid.UUID
    start_at: datetime

class StopSniffDetails(BaseModel):
    sniff_id: uuid.UUID
    stop_at: datetime