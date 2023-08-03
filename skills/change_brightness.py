import screen_brightness_control as sbc
from speech.text2speech import speak
from logs.Logging import log
from subprocess import getstatusoutput
from config.get_config import get_config

xdotool_path = get_config(section='default', key='xdotool', fallback='xdotool')
FACTOR = 20

# brightness_change_rate is when a decrease brightness key is pressed by how much brightness get decreases.
# In testing, it was by 5 units
brightness_change_rate = 5


def run(cmd: str) -> tuple:
    status, output = getstatusoutput(cmd)
    return status, output


def set_brightness(value):
    log.debug(f'Setting brightness to {value}')

    curr = get_brightness()
    change_factor = abs(curr - value)
    speak(f'Changing brightness to {value}')

    if curr > value:
        decrease_brightness(factor=change_factor)

    elif curr < value:
        increase_brightness(factor=change_factor)


def get_brightness():
    """
    :return: Only return display of primary monitor/display
    """
    value = sbc.get_brightness()
    log.debug('Current Brightness is {}%'.format(value[0]))
    # speak('Current Brightness is {}%'.format(value[0]))
    return value[0]


def decrease_brightness(factor=FACTOR):
    # current_brightness = sbc.get_brightness()
    # set_brightness(str(current_brightness - FACTOR))
    for _ in range(factor // brightness_change_rate):
        cmd = xdotool_path + ' key XF86MonBrightnessDown'
        run(cmd=cmd)


def increase_brightness(factor=FACTOR):
    # current_brightness = sbc.get_brightness()
    # set_brightness(str(current_brightness + FACTOR))
    for _ in range(factor // brightness_change_rate):
        cmd = xdotool_path + ' key XF86MonBrightnessUp'
        run(cmd=cmd)
