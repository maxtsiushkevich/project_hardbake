import asyncio
from uuid import UUID

from fastapi import HTTPException, status

from api.exceptions.exceptions import UploadNotFoundError, NoStreamsError, DataAlreadySentError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.pcap_processor import UploadStatus, StreamSummary, SendRMQStatus, ProcessStatus
from api.services.packet_processor import PacketProcessor
from api.utils.rabbitmq import RabbitMQClient


class PcapResultService:
    def __init__(self, redis: PcapRedisRepository):
        self.redis = redis

    async def get_upload_status(self, upload_id: UUID) -> UploadStatus:
        result = await self.redis.get_upload_status(upload_id)
        if not result:
            raise UploadNotFoundError
        return result

    async def get_send_status(self, upload_id: UUID) -> UploadStatus:
        result = await self.redis.get_send_rmq_status(upload_id)
        if not result:
            raise UploadNotFoundError
        return result

    async def get_streams(self, upload_id: UUID) -> StreamSummary:
        func_status = await self.redis.get_upload_status(upload_id)
        if not func_status:
            raise UploadNotFoundError

        if not await self.redis.check_processed_status(upload_id):
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="PCAP file is still being processed"
            )

        streams = await self.redis.get_streams(upload_id)
        if not streams:
            raise NoStreamsError

        if not streams.tcp_streams and not streams.udp_streams:
            raise NoStreamsError

        return streams

    async def send_to_rmq(self, upload_id: UUID):
        func_status = await self.redis.get_send_rmq_status(upload_id)
        if func_status and func_status.status == ProcessStatus.Processed:
            raise DataAlreadySentError

        try:
            streams = await self.get_streams(upload_id)
        except UploadNotFoundError as e:
            raise e
        except NoStreamsError as e:
            raise e

        n_streams = streams.to_packets()
        func_status = SendRMQStatus(status=ProcessStatus.Running, upload_id=upload_id)
        await self.redis.update_send_rmq_status(func_status, upload_id)

        try:
            client = RabbitMQClient()
            channel = await client.get_channel()
            packet_processor = PacketProcessor(channel=channel)

            for stream_id, stream in n_streams['tcp_streams'].items():
                packet_processor.send_stream_rmq(stream)

            for stream_id, stream in n_streams['udp_streams'].items():
                packet_processor.send_stream_rmq(stream)

            func_status = SendRMQStatus(status=ProcessStatus.Processed, upload_id=upload_id)
            await self.redis.update_send_rmq_status(func_status, upload_id)

        except Exception as e:
            func_status = SendRMQStatus(status=ProcessStatus.Crashed, upload_id=upload_id, description=str(e))
            await self.redis.update_send_rmq_status(func_status, upload_id)
