from voice2intent import voice_2_intent
from wake_word.wake_word import detect_wake_word
from wake_word.picovoice import porcupine_default, porcupine_custom
from logs.Logging import log
import argparse
from utilities.initial_setup import initial_setup

if __name__ == '__main__':
    # keyboard = Controller()
    # if keyboard.press('a'):
    args = argparse.ArgumentParser()
    args.add_argument('--setup', action='store_true', help='Do initial setup of BABY')
    arguments = args.parse_args()

    if arguments.setup:
        initial_setup()
        exit('Initial setup completed!')
    try:
        while True:
            detect_wake_word()
            voice_2_intent()
    except Exception as e:
        porcupine_default.delete()
        porcupine_custom.delete()
        print(f'Exception occurred. Exception: {e}')
        log.exception(f'Exception occurred in program. Full exception: {e}')
