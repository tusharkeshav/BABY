import screen_brightness_control as sbc
import text2speech

FACTOR = 20


def set_brightness(value):
    try:
        sbc.set_brightness(value)
    except Exception as e:
        print('Exception occured while setting brigthness. Exception: {}'.format(e))
    finally:
        text2speech.speak('Brightness is set to {}%'.format(value))


def get_brightness() -> int:
    value = sbc.get_brightness()
    text2speech.speak('Current Brightness is {}%'.format(value))
    return value


def decrease_brightness():
    current_brightness = sbc.get_brightness()
    set_brightness(str(current_brightness - FACTOR))


def increase_brightness():
    current_brightness = sbc.get_brightness()
    set_brightness(str(current_brightness + FACTOR))

