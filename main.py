import subprocess
import json
# import keyboard
# from pynput.keyboard import Key, Controller
from text2speech import speak
from voice2intent import voice_2_intent
from picovoice import detect_wake_word

if __name__ == '__main__':
    # keyboard = Controller()
    # if keyboard.press('a'):
    detect_wake_word()
    voice_2_intent()
