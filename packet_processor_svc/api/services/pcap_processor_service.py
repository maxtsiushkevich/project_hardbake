import asyncio
from uuid import uuid4, UUID

from scapy.sendrecv import AsyncSniffer
from scapy.sessions import IPSession

from api.exceptions.exceptions import UploadError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.packet_processor import UploadStatus, FileProcessStatus, PcapProcessResult, StreamSummary
from api.services.packet_processor import PacketProcessor
from api.services.tcp_state_tracker import TCPStateTracker


class PcapProcessorService:
    def __init__(self, file_path: str, redis: PcapRedisRepository):
        self.packet_processor = PacketProcessor()
        self.tcp_state_tracker = TCPStateTracker()
        self._file_path = file_path
        self.redis = redis

    async def upload_file(self) -> UploadStatus:
        try:
            upload_id = uuid4()
            status = UploadStatus(status=FileProcessStatus.Running, upload_id=upload_id)

            await self.redis.update_status(status, upload_id)
            await self.redis.update_streams(StreamSummary(tcp_streams={}, udp_streams={}), upload_id)

        except Exception:
            raise UploadError

        asyncio.create_task(self._process_pcap_file(upload_id))
        return status

    async def _process_pcap_file(self, upload_id: UUID):
        try:
            reader = AsyncSniffer(
                session=IPSession,
                prn=self.packet_processor.process_packet,
                store=False,
                offline=self._file_path
            )
            reader.start()
        except Exception:
            status = UploadStatus(status=FileProcessStatus.Crashed, upload_id=upload_id)
            await self.redis.update_status(status, upload_id)
            await self.redis.update_streams(StreamSummary(tcp_streams={}, udp_streams={}), upload_id)
            raise UploadError

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, reader.join)

        await self._on_pcap_file_finished(upload_id)

    async def _on_pcap_file_finished(self, upload_id: UUID):
        status = UploadStatus(status=FileProcessStatus.Processed, upload_id=upload_id)
        streams = StreamSummary(
            tcp_streams=self.packet_processor.tcp_streams,
            udp_streams=self.packet_processor.udp_streams
        )

        await self.redis.update_status(status, upload_id)
        await self.redis.update_streams(streams, upload_id)
