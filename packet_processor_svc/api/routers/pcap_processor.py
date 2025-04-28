import asyncio
from uuid import UUID

from fastapi import APIRouter, status, UploadFile, File, HTTPException
import tempfile
from api.exceptions.exceptions import UploadError, UploadNotFoundError, NoStreamsError, DataAlreadySentError
from api.repository.redis_repository import RedisConnection, PcapRedisRepository
from api.schemas.pcap_processor import UploadStatus, StreamSummary, SendRMQStatus, ProcessStatus
from api.services.pcap_processor_service import PcapProcessorService
from api.services.pcap_result_service import PcapResultService

router = APIRouter(prefix="/pcap", tags=["PCAP Files Processor"])


@router.post("/upload-pcap",
             status_code=status.HTTP_202_ACCEPTED,
             response_model=UploadStatus,
             responses={
                 200: {"description": "OK"},
                 500: {"description": "Error while uploading pcap"},
             }
             )
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


@router.get("/status/{upload_id}",
            status_code=status.HTTP_200_OK,
            response_model=UploadStatus,
            responses={
                200: {"description": "OK"},
                404: {"description": "Upload with request ID not found"},
            }
            )
async def get_status(upload_id: UUID):
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            result = await pcap_result_service.get_upload_status(upload_id)
        except UploadNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return result


@router.post("/send/{upload_id}",
             status_code=status.HTTP_200_OK,
             response_model=SendRMQStatus,
             responses={
                 200: {"description": "OK"},
                 404: {"description": "Upload with request ID not found"},
                 409: {"description": "Upload with request ID already been processed"},
             }
             )
async def send_streams_to_rmq(upload_id: UUID):
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            asyncio.create_task(pcap_result_service.send_to_rmq(upload_id))
        except UploadNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        except NoStreamsError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        except DataAlreadySentError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This file has already been processed.")
    return SendRMQStatus(status=ProcessStatus.Running, upload_id=upload_id)


@router.get("/send/{upload_id}",
            status_code=status.HTTP_200_OK,
            response_model=SendRMQStatus,
            responses={
                200: {"description": "OK"},
                404: {"description": "Upload with request ID not found"},
            }
            )
async def get_send_status(upload_id: UUID):
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            result = await pcap_result_service.get_send_status(upload_id)
        except UploadNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return result


@router.get("/{upload_id}/streams",
            status_code=status.HTTP_200_OK,
            response_model=StreamSummary,
            responses={
                200: {"description": "OK"},
                404: {"description": "Upload with request ID not found"},
            }
            )
async def get_streams(upload_id: UUID):
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            streams = await pcap_result_service.get_streams(upload_id)
        except UploadNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return streams
