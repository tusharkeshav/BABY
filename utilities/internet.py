import socket
from logs.Logging import log

CLOUDFLARE_DNS = "1.1.1.1"
GOOGLE_HTTP = 'google.com'


def is_http_connected(endpoint):
    try:
        s = socket.socket()
        s.connect((endpoint, 443))
        s.close()
        return True
    except:
        return False


def is_connected(hostname):
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(hostname)
        # connect to the host -- tells us if the host is actually reachable
        s = socket.create_connection((host, 80), 2)
        s.close()
        log.debug('Connected to internet')
        return True
    except Exception:
        pass  # we ignore any errors, returning False
    log.debug('Some issue while connecting to internet')
    return False


def check_internet():
    return is_connected(CLOUDFLARE_DNS)


# print(check_internet())
