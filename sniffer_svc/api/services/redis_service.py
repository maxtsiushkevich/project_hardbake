from api.external_services.redis_config import get_redis_connection
from api.schemas.sniffer import SniffDetails, StartSniffDetails, SniffStatus
from datetime import datetime

conn = get_redis_connection()


async def save_sniff_details(details: StartSniffDetails):
    data = SniffDetails(
        interface=details.interface,
        sniff_id=details.sniff_id,
        start_at=details.start_at,
        status=SniffStatus.Running,
    )
    await conn.set(str(details.sniff_id), data.model_dump_json())


async def get_sniff(sniff_id: str) -> SniffDetails | None:
    data = await conn.get(sniff_id)
    if data:
        return SniffDetails.model_validate_json(data)
    return None


async def update_sniff_status(sniff_id: str, new_status: SniffStatus):
    sniff_details = await get_sniff(sniff_id)
    if not sniff_details:
        raise ValueError(f"Sniff details for ID {sniff_id} not found.")

    sniff_details.status = new_status
    await conn.set(str(sniff_id), sniff_details.model_dump_json())


async def stop_sniff_redis(sniff_id: str):
    sniff_details = await get_sniff(sniff_id)
    if not sniff_details:
        raise ValueError(f"No sniff with {sniff_id}.")

    sniff_details.status = SniffStatus.Stopped
    sniff_details.stop_at = datetime.now()
    await conn.set(str(sniff_id), sniff_details.model_dump_json())


async def get_all_sniffs_redis(start_pos: int | None = None, quantity: int | None = None) -> list[SniffDetails]:
    keys = await conn.keys("*")

    if start_pos is not None and quantity is not None:
        keys = keys[start_pos:start_pos + quantity]
    elif start_pos is not None:
        keys = keys[start_pos:]
    elif quantity is not None:
        keys = keys[:quantity]

    sniffs = []
    for key in keys:
        data = await conn.get(key)
        if data:
            sniffs.append(SniffDetails.model_validate_json(data))

    return sniffs