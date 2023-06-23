import subprocess

from logs.Logging import log
from speech.text2speech import speak
from config.get_config import get_config, ConfigValueNotFound

binary_path = get_config('phone', 'kdeconnect')
try:
    DEVICE_NAME = get_config('phone', 'id')
except ConfigValueNotFound:
    DEVICE_NAME = ''

try:
    xclip_path = get_config('default', 'xclip')
except ConfigValueNotFound:
    xclip_path = ''


class NoModuleFound(Exception):
    pass


def run(cmd: str):
    status, output = subprocess.getstatusoutput(cmd)
    return status, output
    pass


def check_install(module) -> bool:
    """
    This will check if the kdeconnect-cli is there or not
    :return:
    """
    cmd = "which " + module
    status, output = run(cmd)
    if status == 0:
        log.debug(f'{module} is installed.')
        return True
    speak('Please install kde connect first.')
    log.error(f'{module} is not installed. Error: {output}')
    return False
    pass


def get_paired_devices() -> list:
    """
    This will list all the devices are paired and reachable.
    :return: List of paired devices
    """
    cmd = binary_path + '-a --name-only'
    status, output = run(cmd=cmd)
    if output == '':
        return []
    else:
        return output.split('\n')


def get_avail_devices() -> list:
    """
    this will list all the devices which are available. It will consider both paired and unpaired devices
    :return:
    """
    cmd = binary_path + '-l --name-only'
    status, output = run(cmd)
    if output == '':
        log.info('No nearby device found.')
        return []
    else:
        log.info('Devices found are : {}'.format(output.split('\n')))
        return output.split('\n')


def discover_devices():
    cmd = binary_path
    pass


def pair_device():
    pass


def ping_device() -> None:
    """
    If id is defined in config file, then it will send ping to that device.
    If id is not found in config, it will send ping to all the devices that are available and reachable in network.
    Note: It assumes the id defined in config file is paired with kdeconnect-cli
    :return: None
    """
    cmd = binary_path + '--name {device_name} --ping'
    if DEVICE_NAME != '' and len(DEVICE_NAME) >= 2:
        log.debug('Device id found in config.ini file.')
        cmd = cmd.format(device_name=DEVICE_NAME)
        run(cmd)
        pass
    else:
        devices = get_avail_devices()
        log.debug(f'Device id not found in config.ini file. Sending ping to all paired and reachable devices. All '
                  f'found devices {devices}')
        for device in devices:
            run(cmd.format(device_name=device))
    pass


def ring_device() -> None:
    """
    If id is defined in config file, then it will ring that device.
    If id is not found in config, it will ring all the devices that are available and reachable in network.
    NOTE: It assumes the id defined in config file is paired with kdeconnect-cli
    :return: None
    """
    cmd = binary_path + '--name {device_name} --ring'
    if DEVICE_NAME != '' and len(DEVICE_NAME) >= 2:
        cmd = cmd.format(device_name=DEVICE_NAME)
        log.debug(f'Device id found in config.ini file. Submitting cmd: {cmd}')
        run(cmd)
        pass
    else:
        devices = get_avail_devices()
        log.debug(f'Device id not found in config.ini file. Ringing all paired and reachable devices. All found devices {devices}')
        for device in devices:
            run(cmd.format(device_name=device))
    pass


def send_clipboard():
    if not check_install(module='xclip') or len(xclip_path) < 2:
        speak('Error sending clipboard. Xclip is not installed or path is not set in config')
        log.error('Xclip is not installed. Unable to send clipboard')
        return
    last_clipboard = run('/usr/bin/xclip -o')
    kde_cmd = binary_path + '--name {device_name} --share-text $clipboard'
    cmd = f'clipboard=$({last_clipboard}) | {kde_cmd}'
    log.debug(f'Executing cmd for sending clipboard: {cmd}')
    if DEVICE_NAME != '' and len(DEVICE_NAME) >= 2:
        log.debug('Device id found in config.ini file.')
        cmd = cmd.format(device_name=DEVICE_NAME, clipboard=last_clipboard)
        run(cmd)
        pass
    else:
        devices = get_avail_devices()
        log.debug(f'Device id not found in config.ini file. Sending ping to all paired and reachable devices. All '
                  f'found devices {devices}')
        for device in devices:
            run(cmd.format(device_name=device))
    pass