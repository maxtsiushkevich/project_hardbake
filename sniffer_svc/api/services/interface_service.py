import psutil
import socket

from api.exceptions.exceptions import InterfaceNotFoundError


class NetworkInterface:

    def __init__(self, name):
        self.name = name
        self.info = self._get_info()
        self.stats = self._get_stats()

    def _get_info(self):
        if_info = psutil.net_if_addrs().get(self.name)

        if not if_info:
            raise InterfaceNotFoundError

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

        if not stats:
            raise InterfaceNotFoundError

        return {
            'bytes_sent': stats.bytes_sent,
            'bytes_received': stats.bytes_recv,
            'packets_sent': stats.packets_sent,
            'packets_received': stats.packets_recv,
            'errors_in': stats.errin,
            'errors_out': stats.errout,
            'dropped_in': stats.dropin,
            'dropped_out': stats.dropout,
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
    def get_interfaces() -> list[NetworkInterface]:
        return [NetworkInterface(name) for name in psutil.net_if_addrs().keys()]

    @staticmethod
    def get_interfaces_json() -> list[dict[str, str]]:
        return [NetworkInterface(name).to_dict() for name in psutil.net_if_addrs().keys()]

    @staticmethod
    def get_interfaces_name_list() -> list[str]:
        interfaces = psutil.net_if_addrs()
        return list(interfaces.keys())
