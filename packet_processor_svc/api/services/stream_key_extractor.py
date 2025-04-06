from scapy.all import Packet
from scapy.layers.inet import TCP, UDP, IP


class StreamKeyExtractor:
    def __init__(self, packet: Packet):
        self.packet = packet

    @property
    # def stream_key(self) -> str | None:
    def stream_key(self):
        if not self.packet.haslayer(IP):
            # return None
            return None, None
        src_ip = self.packet[IP].src
        dst_ip = self.packet[IP].dst

        if self.packet.haslayer(TCP):
            src_port = self.packet[TCP].sport
            dst_port = self.packet[TCP].dport
            proto = 'TCP'
        elif self.packet.haslayer(UDP):
            src_port = self.packet[UDP].sport
            dst_port = self.packet[UDP].dport
            proto = 'UDP'
        else:
            # return None
            return None, None

        # ips_ports = sorted([(src_ip, src_port), (dst_ip, dst_port)])
        # return f"{ips_ports[0][0]}-{ips_ports[1][0]}-{ips_ports[0][1]}-{ips_ports[1][1]}-{proto}"
        return f"{src_ip}-{dst_ip}-{src_port}-{dst_port}-{proto}", f"{dst_ip}-{src_ip}-{dst_port}-{src_port}-{proto}"
