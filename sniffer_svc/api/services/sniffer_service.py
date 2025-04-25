from uuid import UUID
from api.exceptions.exceptions import SniffNotFoundError, SniffAlreadyRunningError, RabbitMQError
from api.schemas.sniffer import SniffStatus, StartSniffDetails
from api.repository.redis_repository import RedisRepository

from api.utils.sniffer_util import SnifferUtil


class SnifferService:

    def __init__(self, redis: RedisRepository):
        self.redis = redis
        self.sniffer_util = SnifferUtil()

    async def start(self, iface: str, sniff_id, time, filters: str | None = None, write_in_file: bool = False):

        if await self.redis.is_sniffer_running(iface):
            raise SniffAlreadyRunningError
        try:
            details = StartSniffDetails(sniff_id=sniff_id, start_at=time, interface=iface)
            await self.redis.save_sniff(details)

            await self.sniffer_util.start_sniffing(sniff_id=sniff_id, iface=iface, filters=filters,
                                                   write_in_file=write_in_file)
        except RabbitMQError as e:
            print("start")
            await self.redis.update_sniff(sniff_id, SniffStatus.Crashed)
            raise e

    async def stop(self, sniff_id: UUID):
        try:
            await self.sniffer_util.stop_sniffing(sniff_id=sniff_id)
        except SniffNotFoundError as e:
            raise e

        result = await self.redis.stop_sniff(sniff_id)
        return result

    async def get_by_status(self, status: SniffStatus):
        result = await self.redis.get_by_status(status)
        return result

    async def get_all(self, start_pos: int | None = None, quantity: int | None = None):
        sniffs = await self.redis.get_all(start_pos, quantity)
        return sniffs

    async def get(self, sniff_id: UUID):
        result = await self.redis.get_sniff(sniff_id)
        return result
