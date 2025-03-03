import json
import pickle
from typing import Any, Coroutine

from api.external_services.redis_config import get_redis_connection
from api.schemas.sniffer import SniffDetails, StartSniffDetails, SniffStatus

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
