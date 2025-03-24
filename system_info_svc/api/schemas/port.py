from typing import Dict
from pydantic import BaseModel


class PortScanResult(BaseModel):
    address: str
    ports: Dict[str, str]
