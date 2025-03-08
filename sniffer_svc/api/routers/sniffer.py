from datetime import datetime

from fastapi import APIRouter
from uuid import UUID
from starlette import status
from fastapi import HTTPException

from api.exceptions.exceptions import SniffNotFoundError
from api.schemas.sniffer import StartSniffDetails, StopSniffDetails, SniffDetails
from api.repository.redis_repository import RedisConnection, RedisRepository
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


@router.patch("/stop")
async def stop_sniff(sniff_id: UUID):
    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)

        try:
            sniff = await sniffer_service.stop(sniff_id)
        except SniffNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"Sniff {sniff_id} not found"
            )

    return sniff


@router.get("/active")
async def get_active_sniff_tasks():
    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)

        results = await sniffer_service.get_active()

        if not results:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return results


@router.get("/all")
async def get_all_sniffs(start_pos: int | None = None, quantity: int | None = None) -> list[SniffDetails]:
    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)

        result = await sniffer_service.get_all(start_pos, quantity)

    if not result:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    return result


@router.get("/{task_id}")
async def get_sniff_details(task_id: UUID):

    async with RedisConnection() as connection:
        conn = connection.redis
        redis = RedisRepository(conn)
        sniffer_service = SnifferService(redis)
        result = await sniffer_service.get(task_id)

    if not result:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return result
