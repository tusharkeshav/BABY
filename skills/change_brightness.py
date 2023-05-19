import screen_brightness_control as sbc
from speech.text2speech import speak
from logs.Logging import log
FACTOR = 20


def set_brightness(value):
    try:
        sbc.set_brightness(value, display=0)
    except Exception as e:
        log.error('Exception occured while setting brigthness. Exception: {}'.format(e))
    finally:
        log.debug('Brightness is set to {}%'.format(value))
        speak('Brightness is set to {}%'.format(value))


def get_brightness():
    """
    :return: Only return display of primary monitor/display
    """
    value = sbc.get_brightness()
    log.debug('Current Brightness is {}%'.format(value[0]))
    speak('Current Brightness is {}%'.format(value[0]))
    return value[0]


def decrease_brightness():
    current_brightness = sbc.get_brightness()
    set_brightness(str(current_brightness - FACTOR))


def increase_brightness():
    current_brightness = sbc.get_brightness()
    set_brightness(str(current_brightness + FACTOR))

