import asyncio
import logging
from typing import Optional

from api.core.logger import logger
from api.schemas.management import ConsumerStatusEnum
from api.services.stream_processor import StreamProcessor


class ConsumerManager:
    def __init__(self, proxy_packet_processor: StreamProcessor):
        self.proxy_packet_processor = proxy_packet_processor
        self.consumer_task: Optional[asyncio.Task] = None
        self.status = ConsumerStatusEnum.NOT_RUNNING

    async def start(self):
        if self.consumer_task and not self.consumer_task.done():
            logger.debug("Consumer already running.")
            self.status = ConsumerStatusEnum.RUNNING
            return {"status": self.status}

        try:
            logger.debug("Starting consumer")
            self.consumer_task = asyncio.create_task(
                self.proxy_packet_processor.start_consuming(
                    callback=self.proxy_packet_processor.stream_processing_callback
                )
            )
            self.status = ConsumerStatusEnum.RUNNING
            logger.debug("Consumer started successfully.")
            return {"status": self.status}
        except Exception as e:
            logger.debug(f"Failed to start consumer: {str(e)}", exc_info=True)
            self.status = ConsumerStatusEnum.NOT_RUNNING
            raise Exception(f"{str(e)}")

    async def stop(self):
        if not self.consumer_task or self.consumer_task.done():
            self.status = ConsumerStatusEnum.NOT_RUNNING
            logger.debug("Consumer is not running")
            return {"status": self.status}

        try:
            logger.debug("Stopping consumer")
            self.consumer_task.cancel()
            try:
                await asyncio.wait_for(self.consumer_task, timeout=5)
                logger.debug("Consumer stopped gracefully")
            except asyncio.CancelledError:
                logger.debug("Consumer task cancelled")
            except asyncio.TimeoutError:
                logger.debug("Consumer task did not cancel gracefully within timeout", exc_info=True)

            self.status = ConsumerStatusEnum.STOPPED
            return {"status": self.status}
        except Exception as e:
            logger.debug(f"Failed to stop consumer: {str(e)}", exc_info=True)
            self.status = ConsumerStatusEnum.NOT_RUNNING
            raise Exception(f"Failed to stop consumer: {str(e)}")
        finally:
            self.consumer_task = None

    def get_status(self):
        logger.debug(f"Consumer status queried: {self.status}")
        return self.status
