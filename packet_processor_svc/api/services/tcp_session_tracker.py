from collections import defaultdict

from api.core.logger import logger
from api.schemas.pcap_processor import TCPFlags


class TCPSessionTracker:
    def __init__(self):
        self.tcp_stream_states = defaultdict(dict)

    def update_tcp_state(self, key: str, flags: int):
        if key not in self.tcp_stream_states:
            logger.debug(f"Initializing state for TCP stream: {key}")
            self.tcp_stream_states[key] = {
                'seen_syn': False,
                'seen_fin': False,
                'fin_count': 0,
                'closed': False
            }

        state = self.tcp_stream_states[key]
        logger.debug(f"Updating TCP state for stream {key}: current flags={flags}")

        if flags & TCPFlags.SYN and not flags & TCPFlags.ACK:
            state['seen_syn'] = True
            state['closed'] = False
            logger.debug(f"SYN detected (no ACK). Marked seen_syn=True for {key}")
        elif flags & TCPFlags.FIN:
            state['fin_count'] += 1
            logger.debug(f"FIN detected. fin_count={state['fin_count']} for {key}")
            if flags & TCPFlags.ACK and state['fin_count'] >= 2:
                state['closed'] = True
                logger.debug(f"Stream {key} marked as closed after FIN/ACK")
        elif flags & TCPFlags.RST:
            state['closed'] = True
            logger.debug(f"RST detected. Stream {key} marked as closed immediately")

        if state['closed']:
            del self.tcp_stream_states[key]
            logger.debug(f"TCP stream closed: {key}")
            return True
        return False
