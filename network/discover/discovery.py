import socket
import threading
import time

from network.network_enums import Network
from network.communicate import peer_server
from network.discover.udp_broadcast import broadcast, close, broadcast_all_ip
from network.discover.udp_listen import listen
from utilities.watchdog import watch_dog

"""
NOTE:
DEVICE1: Who is broadcasting signal
DEVICE2: Who is capturing the broadcast signal

DEVICE1:
- need broadcasting (UDP broadcast)
- need TCP listener (it will listen to command from the device1)

DEVICE2:
- need broadcast listener (for discovery)
- need TCP Socket (to send cmd to TCP listener of DEVICE1)



Flow:
Device1 will broadcast the signal. 
Other device2 will listen to signal

device1 will detect the signal and send the signal to device1 so that device1 will have ip of the device2

"""


def broadcast_device():
    """
    Needed by DEVICE1
    """
    broadcast_all_ip()


def discover_device():
    device_id, ip_address = listen()
    print('found device')

    pass

    # TODO: recheck if we really need reply to DEVICE1
    # if device_id != (None or ''):
    #     # reply to server that we can connect that broadcast message is received.
    #     # kind of acknowledgement
    #     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #
    #     # Connect to Assistant 1's socket
    #     sock.connect((ip_address, Network.TCP_ACKNOWLEDGEMENT.value))
    #
    #     sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    #
    #     sock.send(str(Network.EXIT.value).encode())
    #     sock.close()
    #     pass


def terminate_udp():
    """
    This will get the data from the broadcast receiver.
    Reason for this method so that the broadcaster get to know the ip address of the receiver.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a specific address and port
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.bind(('localhost', Network.TCP_ACKNOWLEDGEMENT.value))

    # Listen for incoming connections
    sock.listen(5)

    # Accept a connection
    sock, address = sock.accept()

    message = sock.recv(1024).decode()

    if str(message) == str(Network.EXIT.value):
        close()

    return address[0]  # return ip of the broadcast receiver


def broadcast_and_connect():
    # Broadcast the signal of device
    _broadcast_device = threading.Thread(target=broadcast_device)
    _broadcast_device.start()

    def tcp_listener():
        _tcp_listener = threading.Thread(target=peer_server.listen_tcp)
        _tcp_listener.start()
        return _tcp_listener

    _tcp_listener = tcp_listener()

    # Starting watchdog to ensure tcp listener is always running
    watch_dog.watch(monitor=_tcp_listener, action=tcp_listener).start()

    # # Discover the signal
    # # Btw this need to be done only when user ask to send cmd to other device
    # _discover_device = threading.Thread(monitor=discover_device)
    # _discover_device.start()
    #
    # # listen to receive reply from broadcast receiver
    # # We don't need terminate the UDP connection as without we can achieve our work
    # _terminate_udp = threading.Thread(monitor=terminate_udp)
    # _terminate_udp.start()

