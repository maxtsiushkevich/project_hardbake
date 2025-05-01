from uuid import UUID
from api.exceptions.exceptions import SniffNotFoundError, SniffAlreadyRunningError, RabbitMQError
from api.schemas.sniffer import SniffStatus, StartSniffDetails
from api.repository.redis_repository import RedisRepository
from api.utils.sniffer_util import SnifferUtil
from api.core.logger import logger


class SnifferService:

    def __init__(self, redis: RedisRepository):
        self.redis = redis
        self.sniffer_util: SnifferUtil = SnifferUtil()
        logger.debug("SnifferService initialized")

    async def start(self, iface: str, sniff_id, time, filters: str | None = None, write_in_file: bool = False):
        logger.debug(f"Attempting to start sniffing: iface={iface}, sniff_id={sniff_id}, filters={filters}")

        if await self.redis.is_sniffer_running(iface):
            logger.debug(f"Sniffer already running on interface {iface}")
            raise SniffAlreadyRunningError

        try:
            details = StartSniffDetails(sniff_id=sniff_id, start_at=time, interface=iface)
            await self.redis.save_sniff(details)
            logger.debug(f"Saved sniff details to Redis: {details}")

            await self.sniffer_util.start_sniffing(
                sniff_id=sniff_id,
                iface=iface,
                filters=filters,
                write_in_file=write_in_file
            )
            logger.debug(f"Started sniffing for sniff_id={sniff_id} on iface={iface}")
        except RabbitMQError as e:
            logger.debug(f"RabbitMQ error during start sniffing for sniff_id={sniff_id}: {e}")
            await self.redis.update_sniff(sniff_id, SniffStatus.Crashed)
            raise e

    async def stop(self, sniff_id: UUID):
        logger.debug(f"Attempting to stop sniffing for sniff_id={sniff_id}")
        try:
            await self.sniffer_util.stop_sniffing(sniff_id=sniff_id)
            logger.debug(f"Successfully stopped sniffing for sniff_id={sniff_id}")
        except SniffNotFoundError as e:
            logger.debug(f"Sniff not found for stopping: sniff_id={sniff_id}")
            raise e

        result = await self.redis.stop_sniff(sniff_id)
        logger.debug(f"Sniff status updated to stopped in Redis for sniff_id={sniff_id}")
        return result

    async def get_by_status(self, status: SniffStatus):
        logger.debug(f"Retrieving sniffs with status={status}")
        result = await self.redis.get_by_status(status)
        logger.debug(f"Found {len(result)} sniffs with status={status}")
        return result

    async def get_all(self, start_pos: int | None = None, quantity: int | None = None):
        logger.debug(f"Retrieving all sniffs from position {start_pos} with quantity {quantity}")
        sniffs = await self.redis.get_all(start_pos, quantity)
        logger.debug(f"Retrieved {len(sniffs)} sniffs from Redis")
        return sniffs

    async def get(self, sniff_id: UUID):
        logger.debug(f"Retrieving sniff with sniff_id={sniff_id}")
        result = await self.redis.get_sniff(sniff_id)
        if result:
            logger.debug(f"Sniff found for sniff_id={sniff_id}")
        else:
            logger.debug(f"Sniff not found for sniff_id={sniff_id}")
        return result
