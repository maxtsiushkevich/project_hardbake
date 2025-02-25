from fastapi import APIRouter
import psutil
import socket

router = APIRouter(prefix="/interfaces", tags=["Interfaces"])


@router.get("/")
async def get_all_interfaces() -> dict[str, list[str]]:
    interfaces = psutil.net_if_addrs()
    return {"interfaces": list(interfaces.keys())}


@router.get("/{iface}")
async def get_interface_description(iface: str) -> dict[str, dict[str, str]]:
    interfaces = psutil.net_if_addrs()

    result = dict()

    for addr in interfaces[iface]:
        family = get_interface_family(addr.family)
        result[family] = {
            "address": addr.address,
            "netmask": addr.netmask or "",
            "broadcast": addr.broadcast or "",
            "p2p": addr.ptp or ""
        }

    return result


def get_interface_family(family):
    families = {
        socket.AF_INET: "ipv4",
        socket.AF_INET6: "ipv6",
        socket.AF_LINK: "mac"
    }
    return families.get(family, "unknown")
