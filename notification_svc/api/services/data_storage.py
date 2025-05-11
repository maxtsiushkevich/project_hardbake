from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.models import Features, Meta
from api.schemas.data_record import DataRecord


async def add_data_record(data_record: DataRecord, db: AsyncSession):
    try:
        metadata = data_record.meta.split(':')
        # ['192.168.100.229', '65.9.66.9', '64004', '443', '6', '1746822503215395700', '70648600']
        meta = Meta(
            src_ip=metadata[0],
            dst_ip=metadata[1],
            src_port=int(metadata[2]),
            dst_port=int(metadata[3]),
            proto=int(metadata[4]),
            timestamp=datetime.fromtimestamp(int(metadata[5]) / 1e9),
            duration=int(metadata[6]) / 1e9,
        )
        db.add(meta)
        await db.commit()
        await db.refresh(meta)

        features = Features(
            id=meta.id,
            protocol=data_record.protocol,
            bwd_packet_length_max=data_record.bwd_packet_length_max,
            bwd_packet_length_min=data_record.bwd_packet_length_min,
            bwd_packet_length_mean=data_record.bwd_packet_length_mean,
            bwd_packet_length_std=data_record.bwd_packet_length_std,
            flow_IAT_std=data_record.flow_IAT_std,
            flow_IAT_max=data_record.flow_IAT_max,
            fwd_IAT_std=data_record.fwd_IAT_std,
            fwd_IAT_max=data_record.fwd_IAT_max,
            min_packet_length=data_record.min_packet_length,
            max_packet_length=data_record.max_packet_length,
            packet_length_std=data_record.packet_length_std,
            packet_length_variance=data_record.packet_length_variance,
            psh_flag_count=data_record.psh_flag_count,
            avg_bwd_segment_size=data_record.avg_bwd_segment_size,
            idle_min=data_record.idle_min,
            idle_mean=data_record.idle_mean,
            idle_max=data_record.idle_max,
        )
        db.add(features)
        await db.commit()
        print("Sample data added.")
    except Exception as e:
        await db.rollback()
        print(f"Error adding sample data: {e}")
