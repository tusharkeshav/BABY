from enum import Enum


class Network(Enum):
    LOCAL_IP = '0.0.0.0'
    BROADCAST_ADDR = '255.255.255.255'

    # port range: 1800 - 1820
    BROADCAST_PORT = 1800
    COMMUNICATION_PORT = 1802
    EXIT = 0
    TCP_ACKNOWLEDGEMENT = 1803

    pass


class PeerToPeerType:
    SERVER = 1
    CLIENT = 2
    pass
