from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from api.exceptions.exceptions import SniffNotFoundError, SniffAlreadyRunningError
from api.schemas.sniffer import SniffListResponse, StartSniffDetails, SniffDetails, SniffStatus, SniffFilter
from api.repository.redis_repository import RedisConnection, RedisRepository
from api.services.sniffer_service import SnifferService

router = APIRouter(prefix="/sniffer", tags=["Sniffer"])


@router.post("/start", status_code=status.HTTP_202_ACCEPTED, response_model=StartSniffDetails)
async def start_sniff(iface: str, filter_params: SniffFilter | None = None):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        bpf_filter = filter_params.to_bpf() if filter_params else None
        try:
            result = await sniffer_service.start(iface, bpf_filter)
        except SniffAlreadyRunningError:
            raise HTTPException(status_code=409, detail=f"Sniff on interface {iface} already running")

    return StartSniffDetails(**result.dict())


@router.patch("/stop", response_model=SniffDetails)
async def stop_sniff(sniff_id: UUID):
    async with RedisConnection() as connection:
        redis = RedisRepository(connection.redis)
        sniffer_service = SnifferService(redis)

        try:
            sniff = await sniffer_service.stop(sniff_id)
        except SniffNotFoundError:
            raise HTTPException(status_code=404, detail=f"Sniff {sniff_id} not found")

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
