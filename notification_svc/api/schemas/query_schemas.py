from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class SortByEnum(str, Enum):
    id = 'id'
    src_ip = 'src_ip'
    dst_ip = 'dst_ip'
    src_port = 'src_port'
    dst_port = 'dst_port'
    proto = 'proto'
    timestamp = 'timestamp'
    duration = 'duration'


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page")


class SortParams(BaseModel):
    sort_by: Optional[SortByEnum] = Field(default="timestamp", description="Field to sort by")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")


class FilterParams(BaseModel):
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    proto: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None


class QueryParams(PaginationParams, SortParams, FilterParams):
    pass


class MetadataResponse(BaseModel):
    id: int
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    proto: int
    timestamp: datetime
    duration: Optional[float]

    class Config:
        from_attributes = True


class FeaturesResponse(BaseModel):
    id: int
    protocol: Optional[int]
    bwd_packet_length_max: Optional[int]
    bwd_packet_length_min: Optional[int]
    bwd_packet_length_mean: Optional[float]
    bwd_packet_length_std: Optional[float]
    flow_IAT_std: Optional[float]
    flow_IAT_max: Optional[int]
    fwd_IAT_std: Optional[float]
    fwd_IAT_max: Optional[int]
    min_packet_length: Optional[int]
    max_packet_length: Optional[int]
    packet_length_std: Optional[float]
    packet_length_variance: Optional[float]
    psh_flag_count: Optional[int]
    avg_bwd_segment_size: Optional[float]
    idle_min: Optional[int]
    idle_mean: Optional[float]
    idle_max: Optional[int]

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List[MetadataResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
