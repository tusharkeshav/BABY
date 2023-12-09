import os
import re
import socket
import subprocess
from time import sleep
from network.network_enums import Network
from network.message import message_format

# port range: 1800 - 1820
MESSAGE = 'device'
# DEVICE_ID = None
DEVICE_ID = 1234567890


path = os.path.dirname(os.path.abspath(__file__))


def broadcast():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print(f'Sending Broadcast to port {Network.BROADCAST_PORT.value}')
    while True:
        sock.sendto(
            bytes(message_format(message=None), "utf-8"),
            (Network.BROADCAST_ADDR.value, Network.BROADCAST_PORT.value)
        )
        sleep(2)


def close():
    print('terminating broadcast server')
    if sock is not None:
        sock.close()


def is_valid_ip(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))


def check_valid_ip(ip_list: list):
    for ip in ip_list:
        if not is_valid_ip(ip):
            ip_list.remove(ip)
    return ip_list


def broadcast_all_ip():
    all_ips = subprocess.check_output(['hostname', '--all-ip-addresses']).decode().split(' ')
    all_ips = check_valid_ip(all_ips)
    msg = b'hello world'
    print(f'sending broadcast')
    while True:
        for ip in all_ips:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((ip, 0))
            sock.sendto(msg, ("255.255.255.255", 1800))
            sock.close()

        sleep(2)

