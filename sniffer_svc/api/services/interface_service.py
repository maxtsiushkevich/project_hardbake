import psutil
import socket


class NetworkInterface:

    def __init__(self, name):
        self.name = name
        self.info = self._get_info()
        self.stats = self._get_stats()

    def _get_info(self):
        if_info = psutil.net_if_addrs().get(self.name)

        result = {}
        for addr in if_info:
            if addr.family == socket.AF_INET:
                result['IPv4'] = addr.address
                result['IPv4_netmask'] = addr.netmask
            elif addr.family == socket.AF_INET6:
                result['IPv6'] = addr.address
            elif addr.family == psutil.AF_LINK:
                result['mac'] = addr.address

        return result

    def _get_stats(self):
        stats = psutil.net_io_counters(pernic=True).get(self.name)

        return {
            'Bytes Sent': stats.bytes_sent,
            'Bytes Received': stats.bytes_recv,
            'Packets Sent': stats.packets_sent,
            'Packets Received': stats.packets_recv,
            'Errors In': stats.errin,
            'Errors Out': stats.errout,
            'Dropped In': stats.dropin,
            'Dropped Out': stats.dropout,
        }

    def get_info(self):
        return self.info

    def get_stats(self):
        return self.stats

    def to_dict(self):
        return {
            'name': self.name,
            'info': self.info,
            'stats': self.stats
        }


class NetworkInterfaces:
    @staticmethod
    def get_interfaces():
        return [NetworkInterface(name) for name in psutil.net_if_addrs().keys()]

    @staticmethod
    def get_interfaces_name_list() -> list[str]:
        interfaces = psutil.net_if_addrs()
        return list(interfaces.keys())
