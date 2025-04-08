from uuid import UUID

from fastapi import HTTPException

from api.exceptions.exceptions import UploadNotFoundError, NoStreamsError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.pcap_processor import UploadStatus, StreamSummary


class PcapResultService:
    def __init__(self, redis: PcapRedisRepository):
        self.redis = redis

    async def get_upload_status(self, upload_id: UUID) -> UploadStatus:
        result = await self.redis.get_upload_status(upload_id)
        if not result:
            raise UploadNotFoundError
        return result

    async def get_streams(self, upload_id: UUID) -> StreamSummary:
        status = await self.redis.get_upload_status(upload_id)
        if not status:
            raise UploadNotFoundError

        if not await self.redis.check_processed_status(upload_id):
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail="PCAP file is still being processed"
            )

        streams = await self.redis.get_streams(upload_id)
        if not streams:
            raise NoStreamsError

        if not streams.tcp_streams and not streams.udp_streams:
            raise NoStreamsError

        return streams
