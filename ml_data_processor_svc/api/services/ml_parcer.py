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

        if not forward and not backward:
            return None

        fwd_sizes = PacketStatistics.lengths(forward)
        bwd_sizes = PacketStatistics.lengths(backward)
        all_sizes = fwd_sizes + bwd_sizes

        fwd_timestamps = PacketStatistics.timestamps(forward)
        all_timestamps = PacketStatistics.timestamps(stream)

        # Packet length stats
        min_packet_length = min(all_sizes) if all_sizes else 0
        max_packet_length = max(all_sizes) if all_sizes else 0
        packet_length_std = statistics.stdev(all_sizes) if len(all_sizes) > 1 else 0.0
        packet_length_variance = statistics.variance(all_sizes) if len(all_sizes) > 1 else 0.0

        # PSH flag count
        psh_flag_count = sum(1 for p in stream if hasattr(p.packet, 'flags') and 'P' in str(p.packet.flags))

        # Avg Bwd Segment Size
        avg_bwd_segment_size = statistics.mean(bwd_sizes) if bwd_sizes else 0.0

        # Idle times (inter-arrival time)
        def idle_times(timestamps: List[int]) -> List[int]:
            if len(timestamps) < 2:
                return [0]
            return [timestamps[i] - timestamps[i - 1] for i in range(1, len(timestamps))]

        iat_all = idle_times(all_timestamps)
        idle_min = min(iat_all) // 1_000_000 if iat_all else 0
        idle_mean = statistics.mean(iat_all) / 1_000_000 if iat_all else 0.0
        idle_max = max(iat_all) // 1_000_000 if iat_all else 0

        # Flow IAT Std and Max
        flow_IAT_std = statistics.stdev(iat_all) / 1_000_000 if len(iat_all) > 1 else 0.0
        flow_IAT_max = max(iat_all) // 1_000_000 if iat_all else 0

        # Fwd IAT Std and Max
        fwd_iat = idle_times(fwd_timestamps)
        fwd_IAT_std = statistics.stdev(fwd_iat) / 1_000_000 if len(fwd_iat) > 1 else 0.0
        fwd_IAT_max = max(fwd_iat) // 1_000_000 if fwd_iat else 0

        # Bwd Packet Length Stats
        bwd_min, bwd_max, bwd_mean, bwd_std = PacketStatistics.stats(bwd_sizes)

        record = DataRecord(
            protocol=stream[0].packet[IP].proto if stream and stream[0].packet.haslayer(IP) else 0,
            bwd_packet_length_max=bwd_max,
            bwd_packet_length_min=bwd_min,
            bwd_packet_length_mean=bwd_mean,
            bwd_packet_length_std=bwd_std,
            flow_IAT_std=flow_IAT_std,
            flow_IAT_max=flow_IAT_max,
            fwd_IAT_std=fwd_IAT_std,
            fwd_IAT_max=fwd_IAT_max,
            min_packet_length=min_packet_length,
            max_packet_length=max_packet_length,
            packet_length_std=packet_length_std,
            packet_length_variance=packet_length_variance,
            psh_flag_count=psh_flag_count,
            avg_bwd_segment_size=avg_bwd_segment_size,
            idle_min=idle_min,
            idle_mean=idle_mean,
            idle_max=idle_max
        )

        print(record)

        return record