from voice2intent import voice_2_intent, broadcast_device, SUBMIT_JOB
from wake_word.wake_word import detect_wake_word
from wake_word.picovoice import porcupine_default, porcupine_custom
from logs.Logging import log
import argparse
from utilities.initial_setup import initial_setup
from network.discover.discovery import broadcast_device, broadcast_and_connect
from utilities.listen_action_on_network import listen_action_on_network
from utilities.pre_checks import pre_checks

if __name__ == '__main__':
    # keyboard = Controller()
    # if keyboard.press('a'):
    args = argparse.ArgumentParser()
    args.add_argument('--setup', action='store_true', help='Do initial setup of BABY')
    arguments = args.parse_args()

    if arguments.setup:
        initial_setup()
        exit('Initial setup completed!')
    pre_checks()
    SUBMIT_JOB.submit(broadcast_and_connect)
    listen_action_on_network()
    try:
        while True:
            detect_wake_word()
            voice_2_intent(network_action='SearchDevice')
    except Exception as e:
        porcupine_default.delete()
        porcupine_custom.delete()
        print(f'Exception occurred. Exception: {e}')
        log.exception(f'Exception occurred in program. Full exception: {e}')
