from config.get_config import get_config
from logs.Logging import log

SECTION = 'wakeWord'


class WakeWorkConfigurationError(Exception):
    pass


def get_wake_word_config():
    return get_config(SECTION, 'wake_word_method')


def detect_wake_word():
    """
    Detect wake word by different methods.
    Current supported methods are mycroft and picovoice.
    Mycroft can be used as free but to use picovoice, it needs to have access keys in config.ini file
    :return: empty response when the wake word is detected.
    """
    method = get_wake_word_config()
    log.debug(f'Using method={method} to detect wake word')
    if method == 'mycroft':
        from wake_word import mycroft
        mycroft.detect_wake_word()
        return
    elif method == 'picovoice':
        from wake_word import picovoice
        picovoice.detect_wake_word()
        return
    else:
        raise WakeWorkConfigurationError()
