from datetime import datetime

from fastapi import APIRouter
from uuid import UUID, uuid4
from starlette import status
from fastapi import HTTPException

from api.schemas.sniffer import StartSniffDetails, StopSniffDetails, SniffDetails, SniffStatus
from api.services.redis_service import save_sniff_details, update_sniff_status, get_sniff
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
    await update_sniff_status(sniff_id, SniffStatus.Stopped)
    return stop_details


@router.put("/pause-sniff")
async def pause_sniff(sniff_id: str) -> dict[str, str]:
    # TODO
    return {
        "status": "paused",
        "sniff_id": sniff_id,
    }


@router.put("/resume-sniff")
async def resume_sniff(sniff_id: str) -> dict[str, str]:
    # TODO
    return {
        "status": "resumed",
        "sniff_id": sniff_id,
    }


@router.get("/all")
async def get_all_sniff_tasks() -> dict[str, list[str]]:
    task_ids = await get_task_ids()
    if not task_ids:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No tasks found.")
    return {"task_ids": task_ids}


@router.get("/status/{task_id}")
async def get_sniff_details(task_id: str):
    details = await get_sniff(task_id)
    return details
