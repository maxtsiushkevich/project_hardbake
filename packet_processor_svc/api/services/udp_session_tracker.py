import time
from collections import defaultdict

from api.core.logger import logger


class UDPSessionTracker:
    def __init__(self, timeout: int = 10):
        """
        :param timeout: session timeout in seconds
        """
        self.timeout = timeout
        self.udp_stream_last_seen = defaultdict(float)
        self.udp_stream_active = defaultdict(bool)

    def update_udp_state(self, key: str):
        current_time = time.time()

        self.udp_stream_last_seen[key] = current_time
        self.udp_stream_active[key] = True
        logger.debug(f"Updated UDP stream {key} last seen at {current_time}")

    def check_expired_sessions(self) -> list:
        current_time = time.time()
        expired_sessions = []

        keys = list(self.udp_stream_last_seen.keys())

        for key in keys:
            if current_time - self.udp_stream_last_seen[key] > self.timeout:
                self.udp_stream_active[key] = False
                expired_sessions.append(key)
                del self.udp_stream_last_seen[key]
                del self.udp_stream_active[key]

        logger.debug(f"Expired UDP sessions count: {len(expired_sessions)}")
        return expired_sessions
