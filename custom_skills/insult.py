import urllib

from speech.text2speech import speak
from logs.Logging import log


def insult():
    speak('shut the door')
    print('Shut up. I\'ll insult you')
    log.info('Hello i m insult')
    pass
