import asyncio
from collections import defaultdict
from uuid import uuid4, UUID

from scapy.layers.inet import TCP, UDP
from scapy.sendrecv import AsyncSniffer
from scapy.sessions import IPSession

from api.exceptions.exceptions import UploadError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.pcap_processor import UploadStatus, FileProcessStatus, StreamSummary
from api.services.stream_key_extractor import StreamKeyExtractor


class PcapProcessorService:
    def __init__(self, file_path: str, redis: PcapRedisRepository):

        self._file_path = file_path
        self.redis = redis

        self.tcp_streams = defaultdict(list)
        self.udp_streams = defaultdict(list)


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
                prn=self.process_packet,
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
        streams = StreamSummary.from_packets(
            tcp_streams=self.tcp_streams,
            udp_streams=self.udp_streams
        )

        print(len(self.tcp_streams))
        print(len(self.udp_streams))

        await self.redis.update_status(status, upload_id)
        await self.redis.update_streams(streams, upload_id)

    def process_packet(self, packet):
        key, alt_key = StreamKeyExtractor(packet).stream_key
        if not key or not alt_key:
            return None

        if packet.haslayer(TCP):
            if key in self.tcp_streams:
                self.tcp_streams[key].append(packet)
            elif alt_key in self.tcp_streams:
                key = alt_key
                self.tcp_streams[key].append(packet)
            else:
                self.tcp_streams[key].append(packet)

        elif packet.haslayer(UDP):
            if key in self.udp_streams:
                self.udp_streams[key].append(packet)
            elif alt_key in self.udp_streams:
                key = alt_key
                self.udp_streams[key].append(packet)
            else:
                self.udp_streams[key].append(packet)
