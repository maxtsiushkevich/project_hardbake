from fastapi import APIRouter, HTTPException
from api.services.interface_service import NetworkInterfaces, NetworkInterface

router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("/")
async def get_all_interfaces() -> dict[str, list[str]]:
    names = NetworkInterfaces.get_interfaces_name_list()
    if not names:
        raise HTTPException(status_code=404, detail="Interfaces not found")
    return {"interfaces": names}


@router.get("/{iface}")
async def get_interface_description(iface: str):
    interface = NetworkInterface(name=iface).to_dict()
    return interface


@router.get("/{iface}/info")
async def get_interface_description(iface: str):
    info = NetworkInterface(name=iface).get_info()
    return info


@router.get("/{iface}/stat")
async def get_interface_description(iface: str):
    stats = NetworkInterface(name=iface).stats
    return stats
