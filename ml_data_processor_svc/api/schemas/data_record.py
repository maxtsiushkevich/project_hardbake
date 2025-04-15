# Feature Name				        Description
from pydantic import BaseModel


# Flow duration			            Duration of the flow in Microsecond
# total Fwd Packet		            Total packets in the forward direction
# total Bwd packets		            Total packets in the backward direction
# total Length of Fwd Packet	    Total size of packet in forward direction
# total Length of Bwd Packet	    Total size of packet in backward direction
# Fwd Packet Length Min 		    Minimum size of packet in forward direction
# Fwd Packet Length Max 		    Maximum size of packet in forward direction
# Fwd Packet Length Mean		    Mean size of packet in forward direction
# Fwd Packet Length Std		        Standard deviation size of packet in forward direction
# Bwd Packet Length Min	    	    Minimum size of packet in backward direction
# Bwd Packet Length Max   		    Maximum size of packet in backward direction
# Bwd Packet Length Mean	    	Mean size of packet in backward direction
# Bwd Packet Length Std		        Standard deviation size of packet in backward direction
# Average Packet Size 	       	    Average size of packet
# Fwd IAT Max		            	Maximum time between two packets sent in the forward direction
# Bwd IAT Max		            	Maximum time between two packets sent in the backward direction


class DataRecord(BaseModel):
    total_fwd_packet: int
    total_bwd_packets: int
    total_length_of_fwd_packet: int
    total_length_of_bwd_packet: int
    fwd_packet_length_min: int
    fwd_packet_length_max: int
    fwd_packet_length_mean: float
    fwd_packet_length_std: float
    bwd_packet_length_min: int
    bwd_packet_length_max: int
    bwd_packet_length_mean: float
    bwd_packet_length_std: float
    average_packet_size: float
    fwd_IAT_max: float
    bwd_IAT_max: float
