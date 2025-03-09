from pydantic import BaseModel, Field
from typing import Optional


class InterfaceInfo(BaseModel):
    IPv4: Optional[str] = Field(None, description="IPv4 address of the interface")
    IPv4_netmask: Optional[str] = Field(None, description="Subnet mask for IPv4")
    IPv6: Optional[str] = Field(None, description="IPv6 address of the interface")
    mac: Optional[str] = Field(None, description="MAC address of the interface")


class InterfaceStats(BaseModel):
    bytes_sent: int = Field(..., description="Total bytes sent")
    bytes_received: int = Field(..., description="Total bytes received")
    packets_sent: int = Field(..., description="Total packets sent")
    packets_received: int = Field(..., description="Total packets received")
    errors_in: int = Field(..., description="Input errors")
    errors_out: int = Field(..., description="Output errors")
    dropped_in: int = Field(..., description="Dropped incoming packets")
    dropped_out: int = Field(..., description="Dropped outgoing packets")


class NetworkInterfaceSchema(BaseModel):
    name: str = Field(..., description="Interface name")
    info: InterfaceInfo
    stats: InterfaceStats


class InterfacesListResponse(BaseModel):
    interfaces: list[str]
