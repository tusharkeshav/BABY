import subprocess
import time
from logs.Logging import log

MUTE = 0
LOWER = 20
RANGE = 20
temp = 20


def _set_volume(volume):
    log.debug("volunw is: " + str(volume))
    subprocess.getoutput('amixer set Master {volume}'.format(volume=volume))


def get_volume():
    """
    :param
    :return: value: e.g: 19
    """
    volume = str(subprocess.getoutput("amixer sget Master | grep -oP '\[\K[^%]+' | head  -1"))
    return volume


def change_volume(volume):
    value = str(volume) + '%'
    _set_volume(value)


def lower_volume():
    change_volume(RANGE)


def increase_volume():
    value = str(RANGE) + '%+'
    _set_volume(value)


def decrease_volume():
    value = str(RANGE) + '%-'
    _set_volume(value)


def raise_volume_to_normal(original_volume):
    """Can be to decrease voice and again raise voice,
    if there is some song/audio running
    """
    _set_volume(original_volume)


def low_then_normal():
    """
    it will decrease volume to 20% and again increase volume to normal/original value
    :return:
    """
    original_volume = str(get_volume()) + '%'
    time.sleep(1)
    raise_volume_to_normal(original_volume)


def mute():
    _set_volume(MUTE)
