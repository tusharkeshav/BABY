from voice2intent import voice_2_intent
from wake_word.picovoice import detect_wake_word, porcupine_default, porcupine_custom

if __name__ == '__main__':
    # keyboard = Controller()
    # if keyboard.press('a'):
    try:
        while True:
            detect_wake_word()
            voice_2_intent()
    except Exception as e:
        print(f'Exception occurred. Exception: {e}')
        porcupine_default.delete()
        porcupine_custom.delete()
