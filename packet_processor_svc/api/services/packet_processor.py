import pickle
from collections import defaultdict

import pika
from scapy.all import Packet
from scapy.layers.inet import UDP, TCP, IP
from api.services.stream_key_extractor import StreamKeyExtractor
from api.services.tcp_session_tracker import TCPSessionTracker


class PacketProcessor:
    def __init__(self, proxy_mode: bool = False, channel=None):
        self.proxy_mode = proxy_mode
        self.tcp_streams = defaultdict(list)
        self.udp_streams = defaultdict(list)

        self.channel = channel

        self.tcp_session_tracker = TCPSessionTracker()

    def process_packet(self, packet: Packet):
        key, alt_key = StreamKeyExtractor(packet).stream_key
        if not key or not alt_key:
            return None

        if packet.haslayer(TCP):
            if key in self.tcp_streams:
                self.tcp_streams[key].append(packet)
            elif alt_key in self.tcp_streams:
                key = alt_key
                self.tcp_streams[alt_key].append(packet)
            else:
                self.tcp_streams[key].append(packet)

            flags = packet[TCP].flags
            is_end = self.tcp_session_tracker.update_tcp_state(key, flags)
            if is_end and self.proxy_mode:
                print(f"Sent to rmq {len(self.tcp_streams[key])} packets")
                print(type(self.tcp_streams[key]))
                self._send_packet_rmq(self.tcp_streams[key])

        elif packet.haslayer(UDP):
            if key in self.udp_streams:
                self.udp_streams[key].append(packet)
            elif alt_key in self.udp_streams:
                self.udp_streams[alt_key].append(packet)
            else:
                self.udp_streams[key].append(packet)

            # real time udp stream boundary allocation

    def _send_packet_rmq(self, stream):
        stream_rmq = pickle.dumps(stream)
        self.channel.basic_publish(
            exchange='packet_processor_svc.processed_packets.fanout',
            routing_key='',
            body=stream_rmq,
            properties=pika.BasicProperties(delivery_mode=2)
        )
