from datetime import datetime

from fastapi import APIRouter
from uuid import UUID, uuid4
from starlette import status
from fastapi import HTTPException

from api.exceptions.exceptions import SniffNotFoundError
from api.schemas.sniffer import StartSniffDetails, StopSniffDetails, SniffDetails
from api.repository.redis_repository import get_sniff, get_all_sniffs_redis, RedisConnection, RedisRepository
from api.services.sniffer_service import SnifferService

router = APIRouter(prefix="/sniffer", tags=["Sniffer"])


@router.post("/start", status_code=status.HTTP_202_ACCEPTED, response_model=StartSniffDetails)
async def start_sniff(iface: str):
    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)
        result = await sniffer_service.start(iface)
    return result


@router.patch("/stop", response_model=StopSniffDetails)
async def stop_sniff(sniff_id: UUID):
    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)

        try:
            await sniffer_service.stop(sniff_id)
        except SniffNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"Sniff {sniff_id} not found"
            )

    return StopSniffDetails(sniff_id=sniff_id, stop_at=datetime.now())


@router.get("/active")
async def get_active_sniff_task_ids() -> dict[str, list[UUID]]:
    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)
        result = await sniffer_service.get_active_sniffs()
        if not result:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return {"task_ids": result}


@router.get("/all")
async def get_all_sniffs(start_pos: int | None = None, quantity: int | None = None) -> list[SniffDetails]:
    if start_pos is not None and start_pos < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid start position.")
    if quantity is not None and quantity < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quantity.")

    sniffs = await get_all_sniffs_redis(start_pos, quantity)

    if not sniffs:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return sniffs


@router.get("/{task_id}")
async def get_sniff_details(task_id: UUID):
    details = await get_sniff(task_id)
    if not details:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return details
