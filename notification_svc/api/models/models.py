from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from api.utils.database import Base
import datetime


class Meta(Base):
    __tablename__ = "meta"

    id = Column(Integer, primary_key=True, index=True)
    src_ip = Column(String, nullable=False)
    dst_ip = Column(String, nullable=False)
    src_port = Column(Integer, nullable=False)
    dst_port = Column(Integer, nullable=False)
    proto = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    duration = Column(Float)  # duration in seconds

    features = relationship("Features", back_populates="meta")


class Features(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    meta_id = Column(Integer, ForeignKey("meta.id"))
    # meta = Column(String)
    protocol = Column(Integer)

    bwd_packet_length_max = Column(Integer)
    bwd_packet_length_min = Column(Integer)
    bwd_packet_length_mean = Column(Float)
    bwd_packet_length_std = Column(Float)
    flow_IAT_std = Column(Float)
    flow_IAT_max = Column(Integer)
    fwd_IAT_std = Column(Float)
    fwd_IAT_max = Column(Integer)
    min_packet_length = Column(Integer)
    max_packet_length = Column(Integer)
    packet_length_std = Column(Float)
    packet_length_variance = Column(Float)
    psh_flag_count = Column(Integer)
    avg_bwd_segment_size = Column(Float)
    idle_min = Column(Integer)
    idle_mean = Column(Float)
    idle_max = Column(Integer)

    meta = relationship("Meta", back_populates="features")
