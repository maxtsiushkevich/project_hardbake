import os
import pickle
import redis.asyncio as redis
from uuid import UUID

from api.core.logger import logger
from api.schemas.pcap_processor import UploadStatus, StreamSummary, ProcessStatus, SendRMQStatus


class RedisConnection:
    def __init__(self):
        host = os.getenv("REDIS_HOST")
        port = os.getenv("REDIS_PORT")
        logger.info(f"Initializing Redis connection to {host}:{port}")
        self.redis = redis.Redis(host=host, port=int(port), db=0)

    @property
    def connection(self):
        return self.redis

    async def __aenter__(self):
        logger.info("Entering Redis connection context")
        return self

    async def __aexit__(self, type, value, traceback):
        logger.info("Closing Redis connection")
        await self.redis.close()


class PcapRedisRepository:
    def __init__(self, conn):
        logger.info("PcapRedisRepository initialized")
        self.connection = conn

    async def update_upload_status(self, status: UploadStatus, upload_id: UUID):
        key_status = f"{upload_id}:upload_status"
        logger.info(f"Updating upload status for {upload_id}. New status: {status.status}")
        await self.connection.set(key_status, pickle.dumps(status))

    async def get_upload_status(self, upload_id: UUID):
        key_status = f"{upload_id}:upload_status"
        logger.info(f"Retrieving upload status for {upload_id}")
        data = await self.connection.get(key_status)
        if not data:
            logger.warning(f"No upload status found for {upload_id}")
        return pickle.loads(data) if data else None

    async def update_send_rmq_status(self, status: SendRMQStatus, upload_id: UUID):
        key_status = f"{upload_id}:send_rmq_status"
        logger.info(f"Updating send RMQ status for {upload_id}")
        await self.connection.set(key_status, pickle.dumps(status))

    async def get_send_rmq_status(self, upload_id: UUID):
        key_status = f"{upload_id}:send_rmq_status"
        logger.info(f"Retrieving send RMQ status for {upload_id}")
        data = await self.connection.get(key_status)
        if not data:
            logger.warning(f"No send RMQ status found for {upload_id}")
        return pickle.loads(data) if data else None

    async def check_processed_status(self, upload_id: UUID) -> bool:
        logger.info(f"Checking processed status for {upload_id}")
        status = await self.get_upload_status(upload_id)
        processed = status is not None and status.status == ProcessStatus.Processed
        logger.info(f"Processed status for {upload_id}: {processed}")
        return processed

    async def update_streams(self, streams: StreamSummary, upload_id: UUID):
        key_streams = f"{upload_id}:streams"
        logger.info(f"Updating streams data for {upload_id}")
        serialized = pickle.dumps(streams)
        await self.connection.set(key_streams, serialized)

    async def get_streams(self, upload_id: UUID) -> StreamSummary | None:
        key_streams = f"{upload_id}:streams"
        logger.info(f"Retrieving streams data for {upload_id}")
        data = await self.connection.get(key_streams)
        if not data:
            logger.warning(f"No streams data found for {upload_id}")
            return None
        try:
            streams = pickle.loads(data)
            return streams
        except (pickle.PickleError, TypeError) as e:
            logger.error(f"Error deserializing streams for {upload_id}: {e}", exc_info=True)
            return None