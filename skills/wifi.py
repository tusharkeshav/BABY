import enum

from voice2intent import *

CMD = 'rfkill {status} wifi'


class Toggle(enum.Enum):
    ON = 'unblock'
    OFF = 'block'


def run(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return status, output


def wifi_ON():
    run(cmd=CMD.format(status=Toggle.ON.value))
    pass


def wifi_OFF():
    run(cmd=CMD.format(status=Toggle.OFF.value))
    pass


def wifi_STATUS():
    cmd = 'rfkill --json --output TYPE,SOFT,HARD list wifi'
    status, output = run(cmd=cmd)
    output = json.loads(output)
    stat = ''
    try:
        # Note: when rfkill turns on wifi, it put one of adapter as hard block. but it get fixed.
        if output['rfkilldevices'][0]['soft'] == 'unblocked' and \
                output['rfkilldevices'][1]['soft'] == 'unblocked':
            stat = 'on'

        elif output['rfkilldevices'][0]['hard'] == 'blocked' and \
                output['rfkilldevices'][1]['hard'] == 'blocked':
            print('Wifi adapter is hard blocked')
            stat = 'OFF'

        else:
            stat = 'OFF'
        speak('Wifi is turned {stat}'.format(stat=stat))
    except Exception as e:
        log.error('Exception occurred while checking wifi status. Exception: {e}'.format(e=e))
        print('Exception occurred while checking wifi status')
        speak('Some issue occurred while checking wifi status')
