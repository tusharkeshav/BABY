# import peer_server
from network.communicate import peer_client
from network.network_enums import Network
from network.discover.udp_listen import listen

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

Here in this module, we are focussing on the DEVICE2

Flow:
Device1 will broadcast the signal. 
Other device2 will listen to signal

device1 will detect the signal and send the signal to device1 so that device1 will have ip of the device2

"""


def discover_device():
    device_id, ip_address = listen()
    print('Found device')

    return device_id, ip_address
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


def send_message(message):
    """
    It's used to send the command to other device
    """
    peer_client.send_message(message)

    pass


def receive_message():
    """
    It's used to get the reply/message from the device
    """
    return peer_client.receive_messages()


def discover_and_send_message(cmd=None):
    # cmd = ''
    device_id, ip_address = discover_device()

    if peer_client.is_socket_closed():
        peer_client.tcp_server(host=ip_address, port=Network.COMMUNICATION_PORT.value)
        if cmd is not None: send_message(cmd)
    else:
        # Add baby feedback that you are already connected to device
        print('Socket is connected. Already connected to device.')
        send_message(cmd)

    pass


# def discover_device():
#     discover_and_send_message(cmd=None)
