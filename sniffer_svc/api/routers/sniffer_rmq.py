from fastapi import APIRouter, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime

from api.exceptions.exceptions import SniffNotFoundError, SniffAlreadyRunningError, RabbitMQError
from api.schemas.sniffer import SniffListResponse, SniffDetails, SniffStatus, SniffFilter, StartSniffDetails
from api.repository.redis_repository import RedisConnection, RedisRepository
from api.services.sniffer_service import SnifferService

router = APIRouter(prefix="/sniffer-rmq", tags=["Sniffer"])


@router.post("/start", status_code=status.HTTP_202_ACCEPTED, response_model=StartSniffDetails)
async def start_sniff(iface: str, write_in_file: bool = False, filter_params: SniffFilter | None = None):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        bpf_filter = filter_params.to_bpf() if filter_params else None
        try:
            sniff_id = uuid4()

            time = datetime.now()
            await sniffer_service.start(iface, sniff_id, time, bpf_filter, write_in_file)
            return StartSniffDetails(sniff_id=sniff_id, start_at=time, interface=iface)
        except SniffAlreadyRunningError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Sniff on interface {iface} already running")
        except RabbitMQError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.patch("/stop", response_model=SniffDetails)
async def stop_sniff(sniff_id: UUID):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        try:
            sniff = await sniffer_service.stop(sniff_id)
        except SniffNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sniff {sniff_id} not found")

    return SniffDetails(**sniff.dict())


@router.get("/all", response_model=SniffListResponse)
async def get_all_sniffs(start_pos: int | None = None, quantity: int | None = None):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        results = await sniffer_service.get_all(start_pos, quantity)
        if not results:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return SniffListResponse(sniffs=results, total=len(results))


@router.get("/{task_id}", response_model=SniffDetails)
async def get_sniff_details(task_id: UUID):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        result = await sniffer_service.get(task_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return SniffDetails(**result.dict())


@router.get("/status/{status}", response_model=SniffListResponse)
async def get_sniffs_by_status(target_status: SniffStatus):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        results = await sniffer_service.get_by_status(target_status)
        if not results:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return SniffListResponse(sniffs=results, total=len(results))
