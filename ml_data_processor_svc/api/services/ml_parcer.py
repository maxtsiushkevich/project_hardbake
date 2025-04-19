import statistics
from typing import List, Optional

from scapy.compat import raw
from scapy.layers.inet import IP

from api.schemas.data_record import DataRecord
from api.schemas.packet_data import PacketData


class PacketSeparator:
    def __init__(self, packet_data: List[PacketData]):
        self.packet_data = packet_data
        self.src_ip: Optional[str] = None
        self.dst_ip: Optional[str] = None

    def separate(self) -> (List[PacketData], List[PacketData]):
        forward, backward = [], []

        for pdata in self.packet_data:
            pkt = pdata.packet
            ip_layer = pkt.getlayer(IP)
            if not ip_layer:
                continue

            if self.src_ip is None or self.dst_ip is None:
                self.src_ip, self.dst_ip = ip_layer.src, ip_layer.dst
                forward.append(pdata)
                continue

            if ip_layer.src == self.src_ip and ip_layer.dst == self.dst_ip:
                forward.append(pdata)
            elif ip_layer.src == self.dst_ip and ip_layer.dst == self.src_ip:
                backward.append(pdata)

        return forward, backward


class PacketStatistics:
    @staticmethod
    def lengths(packets: List[PacketData]) -> List[int]:
        return [len(raw(p.packet)) for p in packets]

    @staticmethod
    def timestamps(packets: List[PacketData]) -> List[int]:
        return [p.timestamp for p in packets]

    @staticmethod
    def max_iat(timestamps: List[int]) -> float:
        if len(timestamps) == 0:
            return 0
        if len(timestamps) == 1:
            return 0
        if len(timestamps) == 2:
            return (timestamps[1] - timestamps[0]) / 1_000_000

        intervals = [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]
        return max(intervals) / 1_000_000

    @staticmethod
    def stats(values: List[int]) -> (int, int, float, float):
        if not values:
            return 0, 0, 0.0, 0.0
        return (
            min(values),
            max(values),
            statistics.mean(values),
            statistics.stdev(values) if len(values) > 1 else 0.0
        )


class MLParser:
    @staticmethod
    async def parsing_task(stream: List[PacketData]) -> DataRecord | None:
        separator = PacketSeparator(stream)
        forward, backward = separator.separate()

        fwd_sizes = PacketStatistics.lengths(forward)
        bwd_sizes = PacketStatistics.lengths(backward)
        all_sizes = fwd_sizes + bwd_sizes

        fwd_timestamps = PacketStatistics.timestamps(forward)
        bwd_timestamps = PacketStatistics.timestamps(backward)

        fwd_stats = PacketStatistics.stats(fwd_sizes)
        bwd_stats = PacketStatistics.stats(bwd_sizes)

        record = DataRecord(
            total_fwd_packet=len(fwd_sizes),
            total_bwd_packets=len(bwd_sizes),
            total_length_of_fwd_packet=sum(fwd_sizes),
            total_length_of_bwd_packet=sum(bwd_sizes),
            fwd_packet_length_min=fwd_stats[0],
            fwd_packet_length_max=fwd_stats[1],
            fwd_packet_length_mean=fwd_stats[2],
            fwd_packet_length_std=fwd_stats[3],
            bwd_packet_length_min=bwd_stats[0],
            bwd_packet_length_max=bwd_stats[1],
            bwd_packet_length_mean=bwd_stats[2],
            bwd_packet_length_std=bwd_stats[3],
            average_packet_size=statistics.mean(all_sizes) if all_sizes else 0.0,
            fwd_IAT_max=PacketStatistics.max_iat(fwd_timestamps),
            bwd_IAT_max=PacketStatistics.max_iat(bwd_timestamps),
        )

        return record if forward or backward else None