import asyncio
import logging
from typing import Optional

from api.schemas.management import ConsumerStatusEnum
from api.services.stream_processor import StreamProcessor


class ConsumerManager:
    def __init__(self, proxy_packet_processor: StreamProcessor):
        self.proxy_packet_processor = proxy_packet_processor
        self.consumer_task: Optional[asyncio.Task] = None
        self.status = ConsumerStatusEnum.NOT_RUNNING

    async def start(self):
        if self.consumer_task and not self.consumer_task.done():
            self.status = ConsumerStatusEnum.RUNNING
            return {"status": self.status}

        try:
            self.consumer_task = asyncio.create_task(
                self.proxy_packet_processor.start_consuming(
                    callback=self.proxy_packet_processor.stream_processing_callback
                )
            )
            self.status = ConsumerStatusEnum.RUNNING
            return {"status": self.status}
        except Exception as e:
            logging.error(f"Failed to start consumer: {str(e)}")
            self.status = ConsumerStatusEnum.NOT_RUNNING
            raise Exception(f"Failed to start consumer: {str(e)}")

    async def stop(self):
        if not self.consumer_task or self.consumer_task.done():
            self.status = ConsumerStatusEnum.NOT_RUNNING
            return {"status": self.status}

        try:
            self.consumer_task.cancel()
            try:
                await asyncio.wait_for(self.consumer_task, timeout=5)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                logging.warning("Consumer task did not cancel gracefully within timeout")

            self.status = ConsumerStatusEnum.STOPPED
            return {"status": self.status}
        except Exception as e:
            logging.error(f"Failed to stop consumer: {str(e)}")
            self.status = ConsumerStatusEnum.NOT_RUNNING
            raise Exception(f"Failed to stop consumer: {str(e)}")
        finally:
            self.consumer_task = None

    def get_status(self):
        return self.status
