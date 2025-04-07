from collections import defaultdict
from scapy.all import Packet
from scapy.layers.inet import UDP, TCP
from api.services.stream_key_extractor import StreamKeyExtractor


class PacketProcessor:
    def __init__(self):
        self.tcp_streams = defaultdict(list)
        self.udp_streams = defaultdict(list)

    def process_packet(self, packet: Packet):
        key, alt_key = StreamKeyExtractor(packet).stream_key
        if not key or not alt_key:
            return None

        if packet.haslayer(TCP):
            if key in self.tcp_streams:
                self.tcp_streams[key].append(packet)
            elif alt_key in self.tcp_streams:
                self.tcp_streams[alt_key].append(packet)
            else:
                self.tcp_streams[key].append(packet)

        elif packet.haslayer(UDP):
            if key in self.udp_streams:
                self.udp_streams[key].append(packet)
            elif alt_key in self.udp_streams:
                self.udp_streams[alt_key].append(packet)
            else:
                self.udp_streams[key].append(packet)
