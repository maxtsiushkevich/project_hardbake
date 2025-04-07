from uuid import UUID

from api.exceptions.exceptions import UploadNotFoundError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.packet_processor import UploadStatus


class PcapStatusService:
    def __init__(self, redis: PcapRedisRepository):
        self.redis = redis

    async def get_upload_status(self, upload_id: UUID) -> UploadStatus:
        result = await self.redis.get_upload_status(upload_id)
        if not result:
            raise UploadNotFoundError
        return result
