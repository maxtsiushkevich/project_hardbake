import asyncio
from typing import Optional

from api.core.logger import logger
from api.schemas.management import ConsumerStatusEnum
from api.services.proxy_packet_processor import ProxyPacketProcessor


class ConsumerManager:
    def __init__(self, proxy_packet_processor: ProxyPacketProcessor):
        self.proxy_packet_processor = proxy_packet_processor
        self.consumer_task: Optional[asyncio.Task] = None
        self.status = ConsumerStatusEnum.NOT_RUNNING
        logger.debug("ConsumerManager initialized")

    async def start(self, udp_timeout: int):
        logger.debug("Attempting to start consumer")
        if self.consumer_task and not self.consumer_task.done():
            logger.debug("Consumer is already running")
            self.status = ConsumerStatusEnum.RUNNING
            return {"status": self.status}

        try:
            self.consumer_task = asyncio.create_task(
                self.proxy_packet_processor.start_consuming(
                    callback=self.proxy_packet_processor.packet_processing_callback,
                    udp_timeout=udp_timeout
                )
            )
            self.status = ConsumerStatusEnum.RUNNING
            logger.debug("Consumer started successfully")
            return {"status": self.status}
        except Exception as e:
            logger.debug(f"Failed to start consumer: {str(e)}", exc_info=True)
            self.status = ConsumerStatusEnum.ERROR
            raise Exception(f"Failed to start consumer: {str(e)}")

    async def stop(self):
        logger.debug("Attempting to stop consumer")
        if not self.consumer_task or self.consumer_task.done():
            self.status = ConsumerStatusEnum.NOT_RUNNING
            return {"status": self.status}

        try:
            self.consumer_task.cancel()
            try:
                await asyncio.wait_for(self.consumer_task, timeout=5)
                logger.debug("Consumer stopped gracefully")
            except asyncio.CancelledError:
                logger.debug("Consumer task was cancelled")
            except asyncio.TimeoutError:
                logger.debug("Consumer task did not cancel gracefully within timeout", exc_info=True)

            self.status = ConsumerStatusEnum.STOPPED
            return {"status": self.status}
        except Exception as e:
            logger.debug(f"Failed to stop consumer: {str(e)}", exc_info=True)
            self.status = ConsumerStatusEnum.ERROR
            raise Exception(f"Failed to stop consumer: {str(e)}")
        finally:
            self.consumer_task = None
            logger.debug("Consumer task reference cleared")

    def get_status(self):
        logger.debug(f"Returning consumer status: {self.status}")
        return self.status
