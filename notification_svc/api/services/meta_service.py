from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from api.models.models import Meta, Features
from api.schemas.query_schemas import QueryParams


class MetadataService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_meta_with_features(self, meta_id: int) -> Optional[Tuple[Meta, Features]]:
        async with self.db as session:
            query = select(Meta, Features).join(Features).where(Meta.id == meta_id)
            result = await session.execute(query)
            return result.first()

    async def get_meta_list(self, query_params: QueryParams) -> Tuple[List[Meta], int]:
        async with self.db as session:
            query = select(Meta)

            filters = []
            if query_params.src_ip:
                filters.append(Meta.src_ip == query_params.src_ip)
            if query_params.dst_ip:
                filters.append(Meta.dst_ip == query_params.dst_ip)
            if query_params.src_port:
                filters.append(Meta.src_port == query_params.src_port)
            if query_params.dst_port:
                filters.append(Meta.dst_port == query_params.dst_port)
            if query_params.proto:
                filters.append(Meta.proto == query_params.proto)
            if query_params.start_time:
                filters.append(Meta.timestamp >= query_params.start_time)
            if query_params.end_time:
                filters.append(Meta.timestamp <= query_params.end_time)
            if query_params.min_duration:
                filters.append(Meta.duration >= query_params.min_duration)
            if query_params.max_duration:
                filters.append(Meta.duration <= query_params.max_duration)

            if filters:
                query = query.where(and_(*filters))

            # Apply sorting
            sort_column = getattr(Meta, query_params.sort_by, Meta.timestamp)
            if query_params.sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # Get total count
            count_query = select(func.count()).select_from(Meta)
            if filters:
                count_query = count_query.where(and_(*filters))
            total = await session.scalar(count_query)

            query = query.offset((query_params.page - 1) * query_params.page_size).limit(query_params.page_size)

            result = await session.execute(query)
            items = result.scalars().all()

            return items, total

    async def get_statistics(self) -> dict:
        async with self.db as session:
            # Get basic statistics
            stats_query = select(
                func.count().label('total_records'),
                func.avg(Meta.duration).label('avg_duration'),
                func.min(Meta.duration).label('min_duration'),
                func.max(Meta.duration).label('max_duration'),
                func.count(func.distinct(Meta.src_ip)).label('unique_src_ips'),
                func.count(func.distinct(Meta.dst_ip)).label('unique_dst_ips'),
                func.count(func.distinct(Meta.proto)).label('unique_protocols')
            )
            stats = await session.execute(stats_query)
            stats_row = stats.first()

            top_src_ips_query = select(
                Meta.src_ip,
                func.count().label('count')
            ).group_by(Meta.src_ip).order_by(desc('count')).limit(5)
            top_src_ips = await session.execute(top_src_ips_query)
            top_src_ips_list = [{"ip": ip, "count": count} for ip, count in top_src_ips]

            top_dst_ips_query = select(
                Meta.dst_ip,
                func.count().label('count')
            ).group_by(Meta.dst_ip).order_by(desc('count')).limit(5)
            top_dst_ips = await session.execute(top_dst_ips_query)
            top_dst_ips_list = [{"ip": ip, "count": count} for ip, count in top_dst_ips]

            return {
                "total_records": stats_row.total_records,
                "avg_duration": float(stats_row.avg_duration) if stats_row.avg_duration else 0,
                "min_duration": float(stats_row.min_duration) if stats_row.min_duration else 0,
                "max_duration": float(stats_row.max_duration) if stats_row.max_duration else 0,
                "unique_src_ips": stats_row.unique_src_ips,
                "unique_dst_ips": stats_row.unique_dst_ips,
                "unique_protocols": stats_row.unique_protocols,
                "top_source_ips": top_src_ips_list,
                "top_destination_ips": top_dst_ips_list
            } 