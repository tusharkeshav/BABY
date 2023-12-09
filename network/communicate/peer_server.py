import socket
import threading
from network.network_enums import Network


sock: socket.socket = None


def create_connection(host: str, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # Bind the socket to a specific address and port
    server_socket.bind((host, port))

    # Listen for incoming connections
    server_socket.listen(5)

    print('Listening to TCP Conn at port: 1802 ...')

    # Accept a connection
    client_socket, client_address = server_socket.accept()

    return client_socket


# Function to handle incoming messages
def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
            print(f'Received from Assistant 2: {message}')
        except ConnectionResetError:
            print('Connection break with client')
            break


def send_message(message):
    # Send messages to Assistant 2

    sock.send(message.encode())


def is_socket_closed(sock: socket.socket) -> bool:
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
        if len(data) == 0:
            return True
    except BlockingIOError:
        return False  # socket is open and reading from it would block
    except ConnectionResetError:
        return True  # socket was closed for some other reason
    except Exception as e:
        print("unexpected exception when checking if a socket is closed")
        return False
    return False


def listen_tcp():
    # Accept a connection
    global sock
    sock = create_connection(host='localhost', port=Network.COMMUNICATION_PORT.value)

    # Start a thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(sock,))
    receive_thread.start()

    # print(is_socket_closed(client_socket))
