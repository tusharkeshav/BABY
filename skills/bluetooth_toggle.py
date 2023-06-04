from voice2intent import *
from logs.Logging import log


def run(cmd) -> list:
    status, output = subprocess.getstatusoutput(cmd)
    return status, output


def bluetooth_OFF():
    cmd = 'rfkill block bluetooth'
    status = run(cmd=cmd)[0]
    log.debug('Bluetooth off command submitted.')
    if int(status) == 0:
        speak('Bluetooth is set to turn off')
    else:
        speak('Somthing went wrong, while turning Off bluetooth')
    pass


def bluetooth_ON():
    cmd = 'rfkill unblock bluetooth'
    status = run(cmd=cmd)[0]
    log.debug('Bluetooth ON command submitted.')
    if int(status) == 0:
        speak('Bluetooth is turned On')
    else:
        speak('Somthing went wrong, while turning On bluetooth')
    pass


def bluetooth_STATUS():
    cmd = 'hcitool dev'
    output = run(cmd=cmd)[1]
    check_device = output.split('\n')
    if len(check_device) < 2:
        speak('Blue tooth is OFF')
    else:
        speak('Bluetooth is ON')
    log.debug('Bluetooth status is: {output}'.format(output=output))