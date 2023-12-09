import os

# DEVICE_ID = None
DEVICE_ID = 1234567890

path = os.path.dirname(os.path.abspath(__file__))


def get_device_id():
    global DEVICE_ID
    if DEVICE_ID is None:
        with open(os.path.join(path, '.ID'), 'r') as file:
            DEVICE_ID = file.readline()

    return DEVICE_ID


def set_device_id():
    import uuid

    device_id = str(uuid.uuid4())
    with open(os.path.join(path, '.ID'), 'w') as file:
        file.write(device_id)
        file.close()
