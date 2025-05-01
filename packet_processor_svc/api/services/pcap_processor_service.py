import asyncio
from collections import defaultdict
from uuid import uuid4, UUID

from scapy.layers.inet import TCP, UDP
from scapy.packet import Packet
from scapy.utils import PcapNgReader

from api.core.logger import logger
from api.exceptions.exceptions import UploadError
from api.repository.redis_repository import PcapRedisRepository
from api.schemas.packet_data import PacketData
from api.schemas.pcap_processor import UploadStatus, ProcessStatus, StreamSummary
from api.services.stream_key_extractor import StreamKeyExtractor


class PcapProcessorService:
    def __init__(self, file_path: str, redis: PcapRedisRepository):
        self._file_path = file_path
        self.redis = redis

        self.tcp_streams = defaultdict(list)
        self.udp_streams = defaultdict(list)

        logger.debug(f"PcapProcessorService initialized with file: {file_path}")

    async def upload_file(self) -> UploadStatus:
        try:
            upload_id = uuid4()
            logger.debug(f"Starting pcap upload with ID: {upload_id}")
            status = UploadStatus(status=ProcessStatus.Running, upload_id=upload_id)

            await self.redis.update_upload_status(status, upload_id)
            await self.redis.update_streams(StreamSummary(tcp_streams={}, udp_streams={}), upload_id)

            logger.debug(f"Initial upload status and empty streams saved to Redis for upload_id={upload_id}")

        except Exception as e:
            logger.debug(f"Failed to initialize upload: {e}", exc_info=True)
            raise UploadError

        asyncio.create_task(self._process_pcap_file(upload_id))
        return status

    async def _process_pcap_file(self, upload_id: UUID):
        try:
            logger.debug(f"Processing pcap file for upload_id={upload_id}")
            loop = asyncio.get_running_loop()
            with PcapNgReader(self._file_path) as pcap_reader:
                for packet in pcap_reader:
                    try:
                        await loop.run_in_executor(None, self.process_packet, packet)
                    except Exception as e:
                        logger.debug(f"Error processing packet: {e}", exc_info=True)
                        continue

        except Exception as e:
            logger.debug(f"Exception while processing pcap file: {e}", exc_info=True)
            status = UploadStatus(status=ProcessStatus.Crashed, upload_id=upload_id)
            await self.redis.update_upload_status(status, upload_id)
            await self.redis.update_streams(StreamSummary(tcp_streams={}, udp_streams={}), upload_id)
            raise UploadError(f"Failed to process pcap file: {e}")

        await self._on_pcap_file_finished(upload_id)

    async def _on_pcap_file_finished(self, upload_id: UUID):
        logger.debug(f"Finished processing pcap file. upload_id={upload_id}")
        status = UploadStatus(status=ProcessStatus.Processed, upload_id=upload_id)
        streams = StreamSummary.from_packets(
            tcp_streams=self.tcp_streams,
            udp_streams=self.udp_streams
        )

        await self.redis.update_upload_status(status, upload_id)
        await self.redis.update_streams(streams, upload_id)

        logger.debug(f"Final status and stream data saved to Redis. upload_id={upload_id}")

    def process_packet(self, packet: Packet):
        timestamp = int(packet.time * 1_000_000_000)
        packet_data = PacketData(packet=packet, timestamp=timestamp)

        key, alt_key = StreamKeyExtractor(packet).stream_key
        if not key or not alt_key:
            logger.debug(f"Packet {packet} does not contain valid stream keys")
            return None

        if packet.haslayer(TCP):
            logger.debug(f"Processing TCP packet with key={key}")
            if key in self.tcp_streams:
                self.tcp_streams[key].append(packet_data)
            elif alt_key in self.tcp_streams:
                key = alt_key
                self.tcp_streams[key].append(packet_data)
            else:
                self.tcp_streams[key].append(packet_data)

        elif packet.haslayer(UDP):
            logger.debug(f"Processing UDP packet with key={key}")
            if key in self.udp_streams:
                self.udp_streams[key].append(packet_data)
            elif alt_key in self.udp_streams:
                key = alt_key
                self.udp_streams[key].append(packet_data)
            else:
                self.udp_streams[key].append(packet_data)
