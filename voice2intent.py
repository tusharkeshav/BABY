import json
import subprocess
# from log import log
from concurrent.futures import ThreadPoolExecutor

import change_brightness
import coin_flip
import date_time
import media
import random_number
import roll_dice
import stopwatch
import timer
import weather
from text2speech import speak

SUBMIT_JOB = ThreadPoolExecutor(max_workers=5)


def run(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return output


def voice_2_intent():
    speak('Recording voice')
    record = run('timeout 5 arecord -q -r 16000 -c 1 -f S16_LE -t wav /tmp/abc.wav')
    voice2json = run('/usr/bin/voice2json transcribe-wav < /tmp/abc.wav | voice2json recognize-intent')
    voice2json = json.loads(voice2json)
    print(voice2json)
    intent = str(voice2json['intent']['name'])
    if intent == 'Terminal':
        speak('Opening terminal')
        cmd = 'gnome-terminal'
        run(cmd)

    elif intent == 'SetBrightness':
        value = str(voice2json['slots'].get('brightness', 0))
        speak('Changing bright Brightness to {value}'.format(value=value))
        curr_brightness = change_brightness.get_brightness()
        print('value is {}'.format(value))
        if int(curr_brightness) > int(value):
            speak('Increaing brightness to {value}'.format(value=value))
        else:
            speak(f'Decreasing brightness to {value}'.format(value=value))
        change_brightness.increase_brightness(value)

    elif intent == 'IncreaseBrightness':
        value = str(voice2json['slots'].get('brightness', 0))
        speak('Increasing Brightness')
        change_brightness.decrease_brightness()

    elif intent == 'DecreaseBrightness':
        value = str(voice2json['slots'].get('brightness', 0))
        speak('Increasing Brightness')
        change_brightness.increase_brightness(value)

    elif intent == 'CheckWeather':
        weather.get_weather()

    elif intent == 'RainSnow':
        weather.get_rain_snow()

    elif intent == 'Time':
        date_time.get_time()

    elif intent == 'Date':
        date_time.get_date()

    elif intent == 'RandomNumber':
        random_number.get_random_number()

    elif intent == 'Timer':
        SUBMIT_JOB.submit(timer.main)

    elif intent == 'StopWatch':
        SUBMIT_JOB.submit(stopwatch.main)

    elif intent == 'CoinFlip':
        SUBMIT_JOB.submit(coin_flip.flip_coin)
        pass

    elif intent == 'RollDice':
        SUBMIT_JOB.submit(roll_dice.dice_roll)

    elif intent == 'Media':
        print('Found Media intent')
        value = str(voice2json['slots'].get('status', 0))
        print(value)
        if value in ('resume', 'pause', 'stop', 'play'):
            print("value is {}".format(value))
            SUBMIT_JOB.submit(media.pause_resume_toggle)
        elif value == 'mute':
            SUBMIT_JOB.submit(media.mute)
        elif value == 'next':
            SUBMIT_JOB.submit(media.next_media)
        elif value == 'previous':
            SUBMIT_JOB.submit(media.previous_media)

    elif intent == 'Volume':
        pass



    else:
        speak('Command not found')
