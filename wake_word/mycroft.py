from subprocess import getstatusoutput
from logs.Logging import log


class MyCroftWordDetectionExecutionFailed(Exception):
    pass


def _run(cmd):
    status, output = getstatusoutput(cmd)
    return status, output


def detect_wake_word():
    print('*********** Starting Recording and checking for waking word ************')
    log.debug('*********** Starting Recording and checking for waking word ************')
    cmd = '/usr/bin/voice2json wait-wake --exit-count 1'
    status, output = _run(cmd)
    if status == 0:
        return True
    else:
        raise MyCroftWordDetectionExecutionFailed()
