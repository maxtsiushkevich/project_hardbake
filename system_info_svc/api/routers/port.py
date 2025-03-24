from fastapi import APIRouter

router = APIRouter(prefix="/ports", tags=["Port Scanner"])


@router.get("/scan")
async def scan_ports():
    pass
