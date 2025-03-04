from datetime import datetime

from fastapi import APIRouter
from uuid import UUID, uuid4
from starlette import status
from fastapi import HTTPException

from api.schemas.sniffer import StartSniffDetails, StopSniffDetails, SniffDetails
from api.services.redis_service import save_sniff_details, get_sniff, get_all_sniffs_redis, \
    stop_sniff_redis
from api.services.sniffer_service import run_async_sniffer, stop_async_sniffer, get_task_ids

router = APIRouter(prefix="/sniffer", tags=["Sniffer"])


@router.put("/start-sniff", status_code=status.HTTP_202_ACCEPTED, response_model=StartSniffDetails)
async def start_sniff(iface: str):
    sniff_id = uuid4()

    start_details = StartSniffDetails(sniff_id=sniff_id, start_at=datetime.now(), interface=iface)

    await save_sniff_details(start_details)

    await run_async_sniffer(str(sniff_id), iface)
    return start_details


@router.put("/stop-sniff", response_model=StopSniffDetails)
async def stop_sniff(sniff_id: str):
    if not await stop_async_sniffer(sniff_id):
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail=f"Task {sniff_id} already stopped.")

    stop_details = StopSniffDetails(sniff_id=UUID(sniff_id), stop_at=datetime.now())
    await stop_sniff_redis(sniff_id)
    return stop_details

@router.get("/active-ids")
async def get_active_sniff_task_ids() -> dict[str, list[str]]:
    task_ids = await get_task_ids()
    if not task_ids:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return {"task_ids": task_ids}


@router.get("/status/{task_id}")
async def get_sniff_details(task_id: str):
    details = await get_sniff(task_id)
    if not details:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return details

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