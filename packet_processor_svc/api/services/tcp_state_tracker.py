from collections import defaultdict
from api.schemas.packet_processor import TCPFlags


class TCPStateTracker:
    def __init__(self):
        self.tcp_stream_states = defaultdict(dict)

    def update_tcp_state(self, key: str, flags: int):
        if key not in self.tcp_stream_states:
            self.tcp_stream_states[key] = {
                'seen_syn': False,
                'seen_fin': False,
                'fin_count': 0,
                'closed': False
            }

        state = self.tcp_stream_states[key]

        if flags & TCPFlags.SYN and not flags & TCPFlags.ACK:
            state['seen_syn'] = True
            state['closed'] = False
        elif flags & TCPFlags.FIN:
            state['fin_count'] += 1
            if flags & TCPFlags.ACK and state['fin_count'] >= 2:
                state['closed'] = True
        elif flags & TCPFlags.RST:
            state['closed'] = True
