from datetime import datetime

from fastapi import APIRouter
import uuid
from starlette import status
from fastapi import HTTPException

from api.core.tasks import tasks
from api.schemas.sniffer import StartSniffDetails, StopSniffDetails
from api.services.sniffer import run_async_sniffer, stop_async_sniffer

router = APIRouter(prefix="/sniffer", tags=["Sniffer"])


@router.put("/start-sniff", status_code=status.HTTP_202_ACCEPTED, response_model=StartSniffDetails)
async def start_sniff(iface: str):
    sniff_id = str(uuid.uuid4())
    sniff_details = {"sniff_id": sniff_id, "start_at": datetime.now().isoformat(), "interface": iface}
    run_async_sniffer(sniff_id, iface)
    return StartSniffDetails(**sniff_details)


@router.put("/stop-sniff", response_model=StopSniffDetails)
async def stop_sniff(sniff_id: str):
    if sniff_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No task {sniff_id} found.")
    if not stop_async_sniffer(sniff_id):
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail=f"Task {sniff_id} already stopped.")
    stop_sniff_details = {"sniff_id": sniff_id, "stop_at": datetime.now().isoformat()}
    return StopSniffDetails(**stop_sniff_details)


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
async def get_all_tasks() -> dict[str, list[str]]:
    if not tasks:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No tasks found.")
    task_ids = list(tasks.keys())
    return {"task_ids": task_ids}
