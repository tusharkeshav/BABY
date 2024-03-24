import socket

from network.network_enums import Network
from network.device_id import get_device_id, set_device_id
from logs.Logging import log

LISTEN_MAX_TIME_LIMIT = 1000

data: str = ''
addr: str = ''


def listen(custom_id=None) -> (data, addr):
    MAX_LIMIT = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(
        (Network.LOCAL_IP.value, Network.BROADCAST_PORT.value)
    )
    print(f'Listening for UDP port: {Network.BROADCAST_PORT.value}')

    while MAX_LIMIT <= LISTEN_MAX_TIME_LIMIT:
        # sock.sendto(bytes("hello", "utf-8"), ip_co)
        data, addr = sock.recvfrom(1024)
        print(f'Received UDP msg: {data} from IP: {addr[0]} and port: {addr[1]}')
        # below we don't wanted to detect loopback request.
        # we need to filter the received broadcast packet from same device
        if len(data) > 0:
            #### msg should be in format:- <device-id>:msg
            data_chunk = data.decode().split(':')
            device_id, data = data_chunk[0], data_chunk[1]
            if str(device_id) != str(get_device_id()) or custom_id is not None:
                print(f'Found device ID: {data} and address: {addr}')
                return data, addr[0]

        MAX_LIMIT += 1

# listen()
