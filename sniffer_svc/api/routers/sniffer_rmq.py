from fastapi import APIRouter, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime

from api.core.logger import logger
from api.exceptions.exceptions import SniffNotFoundError, SniffAlreadyRunningError, RabbitMQError
from api.schemas.sniffer import SniffListResponse, SniffDetails, SniffStatus, SniffFilter, StartSniffDetails
from api.repository.redis_repository import RedisConnection, RedisRepository
from api.services.sniffer_service import SnifferService

router = APIRouter(prefix="/sniffer-rmq", tags=["Sniffer"])


@router.post("/start",
             status_code=status.HTTP_202_ACCEPTED,
             response_model=StartSniffDetails,
             responses={
                 202: {"description": "Sniffer successfully launched"},
                 409: {"description": "Sniffer already running on a given interface"},
                 500: {"description": "Internal server error"},
                 503: {"description": "RabbitMQ not available"},
             }
             )
async def start_sniff(iface: str, write_in_file: bool = False, filter_params: SniffFilter | None = None):
    logger.info(f"Received request to start sniffing on interface '{iface}' with write_in_file={write_in_file}")
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        bpf_filter = filter_params.to_bpf() if filter_params else None
        if bpf_filter:
            logger.debug(f"BPF filter applied: {bpf_filter}")
        try:
            sniff_id = uuid4()

            time = datetime.now()
            await sniffer_service.start(iface, sniff_id, time, bpf_filter, write_in_file)
            logger.info(f"Started sniffing session {sniff_id} on interface {iface}")
            return StartSniffDetails(sniff_id=sniff_id, start_at=time, interface=iface)
        except SniffAlreadyRunningError:
            logger.warning(f"Sniffer already running on interface {iface}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Sniff on interface {iface} already running")
        except RabbitMQError as e:
            logger.error(f"RabbitMQ error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/clear_cache",
             status_code=status.HTTP_202_ACCEPTED,
             responses={
                 202: {"description": "Redis cleanup started"},
                 500: {"description": "Internal server error"},
             }
             )
async def clear_sniff_cache():
    logger.info(f"Received request clear Redis cache")
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        try:
            await redis.clear_cache()
        except Exception as e:
            logger.error(f"Failed to clear redis cache", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    logger.info(f"Redis cache cleared")

@router.patch("/stop",
              response_model=SniffDetails,
              responses={
                  200: {"description": "OK"},
                  404: {"description": "No sniffing session with the specified ID was found"},
              }
              )
async def stop_sniff(sniff_id: UUID):
    logger.info(f"Received request to stop sniffing session {sniff_id}")
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        try:
            sniff = await sniffer_service.stop(sniff_id)
            logger.info(f"Stopped sniffing session {sniff_id}")
        except SniffNotFoundError:
            logger.warning(f"Sniffing session {sniff_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sniff {sniff_id} not found")

    return SniffDetails(**sniff.dict())


@router.get("/all",
            response_model=SniffListResponse,
            responses={
                200: {"description": "OK"},
                204: {"description": "There are no running sniffing sessions"},
            }
            )
async def get_all_sniffs(start_pos: int | None = None, quantity: int | None = None):
    logger.info(f"Fetching all sniffs (start_pos={start_pos}, quantity={quantity})")
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        results = await sniffer_service.get_all(start_pos, quantity)
        if not results:
            logger.info("No sniffing sessions found")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    logger.info(f"Fetched {len(results)} sniffing sessions")
    return SniffListResponse(sniffs=results, total=len(results))


@router.get("/{task_id}",
            response_model=SniffDetails,
            responses={
                200: {"description": "OK"},
                404: {"description": "There is no sniffing session with the specified ID was found"},
            }
            )
async def get_sniff_details(task_id: UUID):
    logger.info(f"Fetching details for sniffing session {task_id}")
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        result = await sniffer_service.get(task_id)
        if not result:
            logger.warning(f"Sniffing session {task_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sniff {task_id} not found")

    logger.info(f"Fetched details for session {task_id}")
    return SniffDetails(**result.dict())


@router.get("/status/{target_status}",
            response_model=SniffListResponse,
            responses={
                200: {"description": "OK"},
                204: {"description": "There are no sniffing sessions with the specified status was found"},
            }
            )
async def get_sniffs_by_status(target_status: SniffStatus):
    logger.info(f"Fetching sniffing sessions with status: {target_status}")
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        results = await sniffer_service.get_by_status(target_status)
        if not results:
            logger.info(f"No sniffing sessions found with status {target_status}")
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    logger.info(f"Found {len(results)} sessions with status {target_status}")
    return SniffListResponse(sniffs=results, total=len(results))
