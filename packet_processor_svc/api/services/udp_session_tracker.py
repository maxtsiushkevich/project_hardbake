import time
from collections import defaultdict


class UDPSessionTracker:
    def __init__(self, timeout: int):
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

        return expired_sessions
