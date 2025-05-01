from uuid import UUID

from fastapi import HTTPException, status

from api.core.logger import logger
from api.exceptions.exceptions import UploadNotFoundError, NoStreamsError, DataAlreadySentError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.pcap_processor import UploadStatus, StreamSummary, SendRMQStatus, ProcessStatus
from api.services.packet_processor import PacketProcessor
from api.utils.rabbitmq import RabbitMQClient


class PcapResultService:
    def __init__(self, redis: PcapRedisRepository):
        self.redis = redis

    async def get_upload_status(self, upload_id: UUID) -> UploadStatus:
        logger.debug(f"Fetching upload status for upload_id={upload_id}")
        result = await self.redis.get_upload_status(upload_id)
        if not result:
            logger.debug(f"Upload ID not found: {upload_id}")
            raise UploadNotFoundError
        logger.debug(f"Upload status for {upload_id}: {result.status}")
        return result

    async def get_send_status(self, upload_id: UUID) -> UploadStatus:
        logger.debug(f"Fetching send status for upload_id={upload_id}")
        result = await self.redis.get_send_rmq_status(upload_id)
        if not result:
            logger.debug(f"Send status not found for upload ID: {upload_id}")
            raise UploadNotFoundError
        logger.debug(f"Send status for {upload_id}: {result.status}")
        return result

    async def get_streams(self, upload_id: UUID) -> StreamSummary:
        logger.debug(f"Fetching stream data for upload_id={upload_id}")
        func_status = await self.redis.get_upload_status(upload_id)
        if not func_status:
            logger.debug(f"Upload ID not found: {upload_id}")
            raise UploadNotFoundError

        if not await self.redis.check_processed_status(upload_id):
            logger.debug(f"Upload {upload_id} is still being processed")
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="PCAP file is still being processed"
            )

        streams = await self.redis.get_streams(upload_id)
        if not streams or (not streams.tcp_streams and not streams.udp_streams):
            logger.debug(f"No streams found for upload ID: {upload_id}")
            raise NoStreamsError

        logger.debug(f"Streams successfully retrieved for upload_id={upload_id}")
        return streams

    async def send_to_rmq(self, upload_id: UUID):
        logger.debug(f"Initiating send to RMQ for upload_id={upload_id}")
        func_status = await self.redis.get_send_rmq_status(upload_id)

        if func_status and func_status.status == ProcessStatus.Processed:
            logger.debug(f"Data already sent for upload_id={upload_id}")
            raise DataAlreadySentError

        try:
            streams = await self.get_streams(upload_id)
        except (UploadNotFoundError, NoStreamsError) as e:
            logger.debug(f"Stream retrieval failed for upload_id={upload_id}: {e}")
            raise

        n_streams = streams.to_packets()
        func_status = SendRMQStatus(status=ProcessStatus.Running, upload_id=upload_id)
        await self.redis.update_send_rmq_status(func_status, upload_id)

        try:
            client = RabbitMQClient()
            channel = await client.get_channel()
            packet_processor = PacketProcessor(channel=channel)


            tcp_count, udp_count = 0, 0

            for stream_id, stream in n_streams['tcp_streams'].items():
                packet_processor.send_stream_rmq(stream)
                tcp_count += 1

            for stream_id, stream in n_streams['udp_streams'].items():
                packet_processor.send_stream_rmq(stream)
                udp_count += 1

            logger.debug( f"Sent {tcp_count} TCP and {udp_count} UDP streams to RMQ. upload_id={upload_id}")
            func_status = SendRMQStatus(status=ProcessStatus.Processed, upload_id=upload_id)
            await self.redis.update_send_rmq_status(func_status, upload_id)

        except Exception as e:
            logger.debug(f"Failed to send streams to RMQ for upload_id={upload_id}: {e}", exc_info=True)
            func_status = SendRMQStatus(status=ProcessStatus.Crashed, upload_id=upload_id, description=str(e))
            await self.redis.update_send_rmq_status(func_status, upload_id)
