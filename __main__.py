from voice2intent import voice_2_intent
from wake_word.wake_word import detect_wake_word
from wake_word.picovoice import porcupine_default, porcupine_custom
from logs.Logging import log

if __name__ == '__main__':
    # keyboard = Controller()
    # if keyboard.press('a'):
    try:
        while True:
            detect_wake_word()
            voice_2_intent()
    except Exception as e:
        porcupine_default.delete()
        porcupine_custom.delete()
        print(f'Exception occurred. Exception: {e}')
        log.exception(f'Exception occurred in program. Full exception: {e}')
