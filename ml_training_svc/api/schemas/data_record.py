from pydantic import BaseModel


# Feature Name				    Description

# Protocol                      Protocol num (encapsulated in IP)
# Bwd Packet Length Max   		Maximum size of packet in backward direction
# Bwd Packet Length Min	    	Minimum size of packet in backward direction
# Bwd Packet Length Mean	    Mean size of packet in backward direction
# Bwd Packet Length Std		    Standard deviation size of packet in backward direction
# Flow IAT Std	        		Standard deviation time between two packets sent in the flow
# Flow IAT Max		        	Maximum time between two packets sent in the flow
# Fwd IAT Std		           	Standard deviation time between two packets sent in the forward direction
# Fwd IAT Max		            Maximum time between two packets sent in the forward direction
# Min Packet Length 	        Minimum length of a packet
# Max Packet Length 	        Maximum length of a packet
# Packet Length Std		        Standard deviation length of a packet
# Packet Length Variance       	Variance length of a packet
# PSH Flag Count 		        Number of packets with PUSH
# AVG Bwd Segment Size    		Average number of bytes bulk rate in the backward direction
# Idle Min		            	Minimum time a flow was idle before becoming active
# Idle Mean                       Mean time a flow was idle before becoming active
# Idle Max	            		Maximum time a flow was idle before becoming active


class DataRecord(BaseModel):
    protocol: int
    bwd_packet_length_max: int
    bwd_packet_length_min: int
    bwd_packet_length_mean: float
    bwd_packet_length_std: float
    flow_IAT_std: float
    flow_IAT_max: int
    fwd_IAT_std: float
    fwd_IAT_max: int
    min_packet_length: int
    max_packet_length: int
    packet_length_std: float
    packet_length_variance: float
    psh_flag_count: int
    avg_bwd_segment_size: float
    idle_min: int
    idle_mean: float
    idle_max: int
