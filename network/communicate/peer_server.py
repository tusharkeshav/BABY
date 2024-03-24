import socket
import threading
from network.network_enums import Network


sock: socket.socket = None
msg = []


def create_connection(host: str, port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # NOTE: REASON WHY TO USE SO_REUSEADDR?
    # ANS: There is socket time wait. If connection is close non gracefully,
    # it will get into time_wait causing delays and that specific port won't be able
    # to free for use for sometime(probabaly ~4 mins)
    # Similar: https://stackoverflow.com/q/5106674/9730403

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to a specific address and port
    print(f"Creating TCP connection with host: {host} and port: {port}")
    server_socket.bind((host, port))

    # Listen for incoming connections
    server_socket.listen(5)

    print('Listening to TCP Conn at port: 1802 ...')

    # Accept a connection
    client_socket, client_address = server_socket.accept()

    return client_socket


# Function to handle incoming messages
def receive_messages(client_socket=sock):
    print("socket: " +  str(client_socket))
    print(is_socket_closed(client_socket))
    if is_socket_closed(client_socket): print("Client socket is closed")
    while True:
        try:
            if not is_socket_closed(client_socket):
                message = client_socket.recv(1024).decode()
                print(f"message is: {message}")
                if not message:
                    print('Message received is Null. Connection is terminated.')
                    break
                print(f'Received from Assistant 2: {message}')
                global msg
                msg.append(message)
                return message
        except ConnectionResetError:
            print('Connection break with client')
            break


def send_message(message):
    # Send messages to Assistant 2

    sock.send(message.encode())


def is_socket_closed(sock: socket.socket) -> bool:
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


def listen_tcp():
    # Accept a connection
    global sock
    if is_socket_closed(sock):
        print("Printing sock: " + str(sock))
        sock = create_connection(host=Network.LOCAL_IP.value, port=Network.COMMUNICATION_PORT.value)

    # Start a thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(sock,))
    receive_thread.start()

    # print(is_socket_closed(client_socket))


def received_message():
    print('Looking for received message')
    while True:
        if len(msg)!=0:
            return msg