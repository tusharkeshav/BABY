import socket
from network.message import message_deformatter
from logs.Logging import log


sock: socket.socket = None


def _tcp_connect(host: str, port: int):
    MAX_RETRY = 5
    _sock = None
    retry = 1
    while retry <= MAX_RETRY:
        try:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Connect to Assistant 1's socket
            _sock.connect((host, port))

            _sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            return _sock

        except Exception as e:
            if retry == MAX_RETRY:
                print(f'Error occurred while opening TCP socket: {e}')
                raise Exception(f'Error occurred while creating TCP connection.\nException: {e}')
        retry += 1


# Function to handle incoming messages
def receive_messages(sock=sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if not message:
                break
            print(f'Received from Assistant 1: {message}')
            return message_deformatter(message=message)[1]
        except ConnectionResetError:
            print('Connection closed from server')
            break


def tcp_server(host: str, port: int):
    global sock
    if is_socket_closed(sock):
        sock = _tcp_connect(host=host, port=port)
    else:
        print('Socket is still open. Using same socket connection')

    # Start a thread to receive messages
    # receive_thread = threading.Thread(monitor=receive_messages, args=(sock,))
    # receive_thread.start()


def is_socket_closed(sock: socket.socket = sock) -> bool:
    if sock is None:    return True

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


def send_message(message):
    sock.send(message.encode())
