from network.device_id import get_device_id


def message_format(message: [str, None], device_id: str = get_device_id()) -> str:
    return '{}:{}'.format(device_id, message)


def message_deformatter(message: str) -> tuple[str, str]:
    device_id, data = message.split(':')[0], message.split(':')[-1]
    return device_id, data
