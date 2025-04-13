from uuid import UUID

from fastapi import APIRouter, status, UploadFile, File, HTTPException
import tempfile
from api.exceptions.exceptions import UploadError, UploadNotFoundError
from api.repository.redis_repository import RedisConnection, PcapRedisRepository
from api.schemas.pcap_processor import UploadStatus
from api.services.pcap_processor_service import PcapProcessorService
from api.services.pcap_result_service import PcapResultService

router = APIRouter(prefix="/pcap", tags=["PCAP Files Processor"])


@router.post("/upload-pcap", status_code=status.HTTP_202_ACCEPTED, response_model=UploadStatus)
async def upload_pcap(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        packet_pcap_service = PcapProcessorService(tmp_path, redis)
        try:
            result = await packet_pcap_service.upload_file()
        except UploadError:
            raise HTTPException(status_code=500)

    return result


@router.get("/status/{upload_id}", status_code=status.HTTP_200_OK, response_model=UploadStatus)
async def get_status(upload_id: UUID):
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_status_service = PcapResultService(redis)
        try:
            result = await pcap_status_service.get_upload_status(upload_id)
        except UploadNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return result


@router.get("/{upload_id}/streams")
async def get_streams(upload_id: UUID):
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        streams = await redis.get_streams(upload_id)
        if not streams:
            return {"error": "Streams not found"}
    return streams
