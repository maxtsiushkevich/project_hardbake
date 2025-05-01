import psutil
import socket
from api.exceptions.exceptions import InterfaceNotFoundError
from api.core.logger import logger  # Assuming this is your logging setup


class NetworkInterface:
    def __init__(self, name):
        self.name = name
        logger.debug(f"Initializing NetworkInterface for: {name}")
        self._info = self._get_info()
        self._stats = self._get_stats()

    def _get_info(self):
        logger.debug(f"Getting interface info for: {self.name}")
        if_info = psutil.net_if_addrs().get(self.name)

        if not if_info:
            logger.debug(f"Interface {self.name} not found in address list")
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

        logger.debug(f"Interface {self.name} info: {result}")
        return result

    def _get_stats(self):
        logger.debug(f"Getting interface stats for: {self.name}")
        stats = psutil.net_io_counters(pernic=True).get(self.name)

        if not stats:
            logger.debug(f"Interface {self.name} not found in I/O counters")
            raise InterfaceNotFoundError

        result = {
            'bytes_sent': stats.bytes_sent,
            'bytes_received': stats.bytes_recv,
            'packets_sent': stats.packets_sent,
            'packets_received': stats.packets_recv,
            'errors_in': stats.errin,
            'errors_out': stats.errout,
            'dropped_in': stats.dropin,
            'dropped_out': stats.dropout,
        }

        logger.debug(f"Interface {self.name} stats: {result}")
        return result

    @property
    def info(self):
        return self._info

    @property
    def stats(self):
        return self._stats

    def to_dict(self):
        data = {
            'name': self.name,
            'info': self._info,
            'stats': self._stats
        }
        logger.debug(f"Converting interface {self.name} to dict: {data}")
        return data

    @info.setter
    def info(self, value):
        self._info = value

    @stats.setter
    def stats(self, value):
        self._stats = value


class NetworkInterfacesService:
    @staticmethod
    def get_interfaces() -> list[NetworkInterface]:
        logger.debug("Fetching list of NetworkInterface objects")
        interfaces = [NetworkInterface(name) for name in psutil.net_if_addrs().keys()]
        logger.debug(f"Found interfaces: {[iface.name for iface in interfaces]}")
        return interfaces

    @staticmethod
    def get_interfaces_json() -> list[dict[str, str]]:
        logger.debug("Fetching list of network interfaces as JSON")
        interfaces = [NetworkInterface(name).to_dict() for name in psutil.net_if_addrs().keys()]
        logger.debug(f"Interfaces JSON: {interfaces}")
        return interfaces

    @staticmethod
    def get_interfaces_name_list() -> list[str]:
        logger.debug("Fetching interface name list")
        interfaces = psutil.net_if_addrs()
        names = list(interfaces.keys())
        logger.debug(f"Interface names: {names}")
        return names
