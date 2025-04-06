import asyncio
from collections import defaultdict
from uuid import uuid4
from scapy.all import Packet
from scapy.layers.inet import UDP, TCP
from scapy.sendrecv import AsyncSniffer
from scapy.sessions import IPSession
from api.repository.redis_repository import RedisRepository
from api.schemas.packet_processor import TCPFlags, StreamSummary, UploadResult, FileProcessStatus
from api.services.stream_key_extractor import StreamKeyExtractor


class PacketPcapService:
    def __init__(self, file_path: str, redis: RedisRepository):
        self.tcp_streams = defaultdict(list)
        self.tcp_stream_states = defaultdict(dict)
        self.udp_streams = defaultdict(list)
        self._file_path = file_path
        self.redis = redis

    async def upload_file(self):
        upload_id = uuid4()
        details = UploadResult(status=FileProcessStatus.Running, upload_id=upload_id)
        # await self.process_pcap_file()
        asyncio.create_task(self.process_pcap_file())
        return details

    def process_packet(self, packet: Packet) -> str | None:
        # key = StreamKeyExtractor(packet).stream_key
        # if not key:
        #     return None
        #
        # if packet.haslayer(TCP):
        #     self.tcp_streams[key].append(packet)
        #     self._update_tcp_state(key, packet[TCP].flags)
        # elif packet.haslayer(UDP):
        #     self.udp_streams[key].append(packet)
        #
        # return key

        key, alt_key = StreamKeyExtractor(packet).stream_key
        if not key or not alt_key:
            return None

        if packet.haslayer(TCP):
            if key in self.tcp_streams:
                self.tcp_streams[key].append(packet)
            elif alt_key in self.tcp_streams:
                # key = alt_key
                self.tcp_streams[alt_key].append(packet)
            else:
                self.tcp_streams[key].append(packet)

        elif packet.haslayer(UDP):
            if key in self.udp_streams:
                self.udp_streams[key].append(packet)
            elif alt_key in self.udp_streams:
                # key = alt_key
                self.udp_streams[alt_key].append(packet)
            else:
                self.udp_streams[key].append(packet)

    def _update_tcp_state(self, key: str, flags: int):
        if key not in self.tcp_stream_states:
            self.tcp_stream_states[key] = {
                'seen_syn': False,
                'seen_fin': False,
                'fin_count': 0,
                'closed': False
            }

        state = self.tcp_stream_states[key]

        if flags & TCPFlags.SYN and not flags & TCPFlags.ACK:
            state['seen_syn'] = True
            state['closed'] = False
        elif flags & TCPFlags.FIN:
            state['fin_count'] += 1
            if flags & TCPFlags.ACK and state['fin_count'] >= 2:
                state['closed'] = True
        elif flags & TCPFlags.RST:
            state['closed'] = True

    async def process_pcap_file(self):
        reader = AsyncSniffer(session=IPSession, prn=self.process_packet, store=False, offline=self._file_path)
        reader.start()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, reader.join)  # Выполнить в фоновом потоке

        await self.on_sniffer_finished()

    async def on_sniffer_finished(self):
        print(f"Всего TCP-потоков: {len(self.tcp_streams)}")
        print(f"Всего UDP-потоков: {len(self.udp_streams)}")

    def get_stream_summary(self) -> StreamSummary:
        return StreamSummary(
            tcp_streams=self.tcp_streams,
            udp_streams=self.udp_streams
        )
