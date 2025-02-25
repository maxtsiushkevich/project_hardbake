from fastapi import APIRouter
import uuid
from starlette import status

router = APIRouter(prefix="/sniffer", tags=["Sniffer"])


@router.put("/start-sniff", status_code=status.HTTP_202_ACCEPTED)
async def start_sniff(iface: str) -> dict[str, str]:
    sniff_id = uuid.uuid4()
    return {
        "iface": iface,
        "sniff_id": str(sniff_id),
    }


@router.put("/stop-sniff")
async def stop_sniff(sniff_id: str) -> dict[str, str]:
    return {
        "status": "stop",
        "sniff_id": sniff_id,
    }


@router.put("/pause-sniff")
async def pause_sniff(sniff_id: str) -> dict[str, str]:
    return {
        "status": "stopped",
        "sniff_id": sniff_id,
    }


@router.put("/resume-sniff")
async def resume_sniff(sniff_id: str) -> dict[str, str]:
    return {
        "status": "stopped",
        "sniff_id": sniff_id,
    }
