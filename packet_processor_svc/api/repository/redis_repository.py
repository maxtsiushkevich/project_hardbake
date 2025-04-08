import os
import pickle
import redis.asyncio as redis
from uuid import UUID

from api.schemas.pcap_processor import UploadStatus


class RedisConnection:
    def __init__(self):
        host = os.getenv("REDIS_HOST")
        port = os.getenv("REDIS_PORT")
        self.redis = redis.Redis(host=host, port=int(port), db=0)

    @property
    def connection(self):
        return self.redis

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.redis.close()


class PcapRedisRepository:
    def __init__(self, conn):
        self.connection = conn

    async def update_status(self, status: UploadStatus, upload_id: UUID):
        key_status = f"{upload_id}:status"
        await self.connection.set(key_status, pickle.dumps(status))

    # async def update_streams(self, streams: StreamSummary, upload_id: UUID):
    #     key_streams = f"{upload_id}:streams"
    #     await self.connection.set(key_streams, pickle.dumps(streams))

    async def get_upload_status(self, upload_id: UUID):
        key_status = f"{upload_id}:status"
        data = await self.connection.get(key_status)
        return pickle.loads(data) if data else None



