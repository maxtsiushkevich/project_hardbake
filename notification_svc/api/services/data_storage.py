import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.models import Features, Meta
from api.schemas.data_record import DataRecord


async def add_data_record(data_record: DataRecord, db: AsyncSession):
    try:
        meta = Meta(
            src_ip="192.168.0.1",
            dst_ip="192.168.0.100",
            src_port=12345,
            dst_port=80,
            proto=6,
            timestamp=datetime.datetime.utcnow(),
            duration=1.23
        )
        db.add(meta)
        await db.commit()
        await db.refresh(meta)

        features = Features(
            id=meta.id,
            protocol=6,
            bwd_packet_length_max=1000,
            bwd_packet_length_min=500,
            bwd_packet_length_mean=750.0,
            bwd_packet_length_std=100.0,
            flow_IAT_std=15.0,
            flow_IAT_max=100,
            fwd_IAT_std=10.0,
            fwd_IAT_max=80,
            min_packet_length=60,
            max_packet_length=1514,
            packet_length_std=50.0,
            packet_length_variance=2500.0,
            psh_flag_count=2,
            avg_bwd_segment_size=600.0,
            idle_min=10,
            idle_mean=20.5,
            idle_max=30
        )
        db.add(features)
        await db.commit()
        print("Sample data added.")
    except Exception as e:
        await db.rollback()
        print(f"Error adding sample data: {e}")
