import pickle
from collections import defaultdict

import pika
from scapy.all import Packet
from scapy.layers.inet import UDP, TCP

from api.schemas.packet_data import PacketData
from api.services.stream_key_extractor import StreamKeyExtractor
from api.services.tcp_session_tracker import TCPSessionTracker
from api.services.udp_session_tracker import UDPSessionTracker


class PacketProcessor:
    def __init__(self, udp_timeout, proxy_mode: bool = False, channel=None):
        self.proxy_mode = proxy_mode
        self.tcp_streams = defaultdict(list)
        self.udp_streams = defaultdict(list)

        self.channel = channel

        self.tcp_session_tracker = TCPSessionTracker()
        self.udp_session_tracker = UDPSessionTracker(timeout=udp_timeout)

    def process_packet(self, packet_data: PacketData):
        packet: Packet = packet_data.packet

        key, alt_key = StreamKeyExtractor(packet).stream_key
        if not key or not alt_key:
            return None

        if packet.haslayer(TCP):
            if key in self.tcp_streams:
                self.tcp_streams[key].append(packet_data)
            elif alt_key in self.tcp_streams:
                key = alt_key
                self.tcp_streams[key].append(packet_data)
            else:
                self.tcp_streams[key].append(packet_data)

            flags = packet[TCP].flags
            is_end = self.tcp_session_tracker.update_tcp_state(key, flags)

            if is_end and self.proxy_mode:
                stream = self.tcp_streams.pop(key, [])
                if stream:
                    # print(f"{key} TCP")
                    self._send_stream_rmq(stream)

        elif packet.haslayer(UDP):
            if key in self.udp_streams:
                self.udp_streams[key].append(packet_data)
            elif alt_key in self.udp_streams:
                key = alt_key
                self.udp_streams[key].append(packet_data)
            else:
                self.udp_streams[key].append(packet_data)

            self.udp_session_tracker.update_udp_state(key)
            expired_sessions = self.udp_session_tracker.check_expired_sessions()

            for expired_key in expired_sessions:
                stream = self.udp_streams.pop(expired_key, [])
                if stream:
                    # print(f"{expired_key} UDP")
                    self._send_stream_rmq(stream)

    def _send_stream_rmq(self, stream):
        try:
            stream_rmq = pickle.dumps(stream)
            self.channel.basic_publish(
                exchange='packet_processor_svc.processed_packets.fanout',
                routing_key='',
                body=stream_rmq,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except Exception as e:
            print(f"Error while sending message: {e}")
