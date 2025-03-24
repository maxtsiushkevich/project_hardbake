from fastapi import APIRouter, HTTPException

from api.exceptions.exceptions import InterfaceNotFoundError
from api.services.interface_service import NetworkInterfacesService, NetworkInterface
from api.schemas.interface import NetworkInterfaceSchema, InterfacesListResponse, InterfaceInfo, InterfaceStats

router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("/", response_model=InterfacesListResponse)
async def get_interfaces_list():
    names = NetworkInterfacesService.get_interfaces_name_list()
    if not names:
        raise HTTPException(status_code=404, detail="Interfaces not found")
    return InterfacesListResponse(interfaces=names)


@router.get("/all", response_model=list[NetworkInterfaceSchema])
async def get_interfaces():
    interfaces = NetworkInterfacesService.get_interfaces_json()
    if not interfaces:
        raise HTTPException(status_code=404, detail="Interfaces not found")
    return interfaces


@router.get("/{iface}", response_model=NetworkInterfaceSchema)
async def get_interface_description(iface: str):
    try:
        interface = NetworkInterface(name=iface).to_dict()
    except InterfaceNotFoundError:
        raise HTTPException(status_code=404, detail="Interface not found")
    return interface


@router.get("/{iface}/info", response_model=InterfaceInfo)
async def get_interface_info(iface: str):
    try:
        info = NetworkInterface(name=iface).info
    except InterfaceNotFoundError:
        raise HTTPException(status_code=404, detail="Interface not found")
    return info


@router.get("/{iface}/stat", response_model=InterfaceStats)
async def get_interface_stats(iface: str):
    try:
        stats = NetworkInterface(name=iface).stats
    except InterfaceNotFoundError:
        raise HTTPException(status_code=404, detail="Interface not found")
    return stats
