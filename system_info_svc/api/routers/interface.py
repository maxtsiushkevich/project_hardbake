from fastapi import APIRouter, HTTPException

from api.core.logger import logger
from api.exceptions.exceptions import InterfaceNotFoundError
from api.services.interface_service import NetworkInterfacesService, NetworkInterface
from api.schemas.interface import NetworkInterfaceSchema, InterfacesListResponse, InterfaceInfo, InterfaceStats

router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("/",
            response_model=InterfacesListResponse,
            responses={
                200: {"description": "OK"},
                404: {"description": "Interfaces not found"},
            })
async def get_interfaces_list():
    logger.info("Fetching list of network interface names")
    names = NetworkInterfacesService.get_interfaces_name_list()
    if not names:
        logger.warning("No network interfaces found")
        raise HTTPException(status_code=404, detail="Interfaces not found")

    logger.info(f"Founded {len(names)} interfaces")
    return InterfacesListResponse(interfaces=names)


@router.get("/all",
            response_model=list[NetworkInterfaceSchema],
            responses={
                200: {"description": "OK"},
                404: {"description": "Interfaces not found"},
            })
async def get_interfaces():
    logger.info("Fetching detailed interface information for all interfaces")
    interfaces = NetworkInterfacesService.get_interfaces_json()
    if not interfaces:
        logger.warning("No detailed interfaces information found")
        raise HTTPException(status_code=404, detail="Interfaces not found")

    logger.info(f"Found interface details for {len(interfaces)} interfaces")
    return interfaces


@router.get("/{iface}",
            response_model=NetworkInterfaceSchema,
            responses={
                200: {"description": "OK"},
                404: {"description": "Interfaces not found"},
            })
async def get_interface_description(iface: str):
    logger.info(f"Fetching description for interface: {iface}")
    try:
        interface = NetworkInterface(name=iface).to_dict()
    except InterfaceNotFoundError:
        logger.error(f"Interface {iface} not found")
        raise HTTPException(status_code=404, detail="Interface not found")

    logger.info(f"Interface {iface} description retrieved successfully")
    return interface


@router.get("/{iface}/info",
            response_model=InterfaceInfo,
            responses={
                200: {"description": "OK"},
                404: {"description": "Interfaces not found"},
            })
async def get_interface_info(iface: str):
    logger.info(f"Fetching info for interface: {iface}")
    try:
        info = NetworkInterface(name=iface).info
    except InterfaceNotFoundError:
        logger.error(f"Interface {iface} not found")
        raise HTTPException(status_code=404, detail="Interface not found")

    logger.info(f"Info for interface {iface} retrieved successfully")
    return info


@router.get("/{iface}/stat",
            response_model=InterfaceStats,
            responses={
                200: {"description": "OK"},
                404: {"description": "Interfaces not found"},
            })
async def get_interface_stats(iface: str):
    logger.info(f"Fetching stats for interface: {iface}")
    try:
        stats = NetworkInterface(name=iface).stats
    except InterfaceNotFoundError:
        logger.error(f"Interface {iface} not found")
        raise HTTPException(status_code=404, detail="Interface not found")

    logger.info(f"Stats for interface {iface} retrieved successfully")
    return stats
