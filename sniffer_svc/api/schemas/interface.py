from pydantic import BaseModel


class Interface(BaseModel):
    address: str
    netmask: str
    broadcast: str
    p2p: bool


# import ipaddress
#
# def check(ip) -> bool:
#     try:
#         ipaddress.ip_address(ip)
#         return True
#     except ValueError:
#         return False
