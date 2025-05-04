import asyncio
from uuid import UUID

from fastapi import APIRouter, status, UploadFile, File, HTTPException
import tempfile

from api.core.logger import logger
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
    logger.info(f"Received pcap upload request: filename={file.filename}")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
        logger.debug(f"Temporary file created at {tmp_path}")

    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        packet_pcap_service = PcapProcessorService(tmp_path, redis)
        try:
            result = await packet_pcap_service.upload_file()
            logger.info(f"PCAP upload processed successfully, upload_id={result.upload_id}")
        except UploadError as e:
            logger.error(f"UploadError occurred while processing PCAP: {e}", exc_info=True)
            raise HTTPException(status_code=500)

    return result

@router.get("/all",
            status_code=status.HTTP_200_OK,
            response_model=list[UploadStatus],
            responses={
                200: {"description": "OK"},
                204: {"description": "No uploads found"},
            }
            )
async def get_all_uploads(start_pos: int | None = None, quantity: int | None = None):
    logger.info(f"Received request to get all uploads with start_pos={start_pos}, quantity={quantity}")
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            result = await pcap_result_service.get_all_uploads(start_pos, quantity)
            logger.debug(f"Retrieved {len(result)} uploads")
        except HTTPException as e:
            if e.status_code == status.HTTP_204_NO_CONTENT:
                logger.debug("No uploads found")
            raise
    return result

@router.get("/status/{status}",
            status_code=status.HTTP_200_OK,
            response_model=list[UploadStatus],
            responses={
                200: {"description": "OK"},
                204: {"description": "No uploads found with specified status"},
            }
            )
async def get_sniffs_by_status(target_status: ProcessStatus):
    logger.info(f"Received request to get uploads with status={target_status}")
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            result = await pcap_result_service.get_uploads_by_status(target_status)
            logger.debug(f"Retrieved {len(result)} uploads with status {target_status}")
        except HTTPException as e:
            if e.status_code == status.HTTP_204_NO_CONTENT:
                logger.debug(f"No uploads found with status {target_status}")
            raise
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
    logger.info(f"Received request for upload status: upload_id={upload_id}")
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            result = await pcap_result_service.get_upload_status(upload_id)
            logger.debug(f"Upload status retrieved: {result}")
        except UploadNotFoundError:
            logger.warning(f"Upload ID not found: {upload_id}")
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
    logger.info(f"Initiating RMQ stream send for upload_id={upload_id}")
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            asyncio.create_task(pcap_result_service.send_to_rmq(upload_id))
            # await pcap_result_service.send_to_rmq(upload_id)
            logger.info(f"Stream sending task created for upload_id={upload_id}")
        except UploadNotFoundError:
            logger.warning(f"Upload not found for RMQ send: {upload_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        except NoStreamsError as e:
            logger.warning(f"No streams found for upload_id={upload_id}: {e}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        except DataAlreadySentError as e:
            logger.warning(f"Data already sent for upload_id={upload_id}")
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
    logger.info(f"Received request for RMQ send status: upload_id={upload_id}")
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            result = await pcap_result_service.get_send_status(upload_id)
            logger.debug(f"Send RMQ status for upload_id={upload_id}: {result}")
        except UploadNotFoundError:
            logger.warning(f"Upload not found while checking send status: {upload_id}")
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
    logger.info(f"Request received to fetch streams for upload_id={upload_id}")
    async with RedisConnection() as connection:
        redis = PcapRedisRepository(connection.redis)
        pcap_result_service = PcapResultService(redis)
        try:
            logger.debug(f"Retrieved stream summary for upload_id={upload_id}")
            streams = await pcap_result_service.get_streams(upload_id)
        except UploadNotFoundError:
            logger.warning(f"Upload ID not found when retrieving streams: {upload_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return streams
