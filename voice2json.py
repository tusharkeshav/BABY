import subprocess
import json
from threading import Thread

import change_brightness
import stopwatch
import timer
from text2speech import speak
import weather
import date_time


def run(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return output


def voice2json():
    speak('Recording voice')
    record = run('timeout 5 arecord -q -r 16000 -c 1 -f S16_LE -t wav /tmp/abc.wav')
    voice2json = run('voice2json transcribe-wav < /tmp/abc.wav | voice2json recognize-intent')
    voice2json = json.loads(voice2json)
    print(voice2json)
    intent = str(voice2json['intent']['name'])
    if intent == 'Terminal':
        speak('Opening terminal')
        cmd = 'gnome-terminal'
        run(cmd)

    elif intent == 'SetBrightness':
        value = str(voice2json['slot'].get('brightness', 0))
        speak('Changing bright Brightness to {value}'.format(value=value))
        curr_brightness = change_brightness.get_brightness()
        if int(curr_brightness) > int(value):
            speak('Increaing brightness to {value}'.format(value=value))
        else:
            speak(f'Decreasing brightness to {value}'.format(value=value))
        change_brightness.increase_brightness(value)

    elif intent == 'IncreaseBrightness':
        value = str(voice2json['slot'].get('brightness', 0))
        speak('Increasing Brightness')
        change_brightness.decrease_brightness()

    elif intent == 'DecreaseBrightness':
        value = str(voice2json['slot'].get('brightness', 0))
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
        import random_number
        random_number.get_random_number()

    elif intent == 'Timer':
        t1 = Thread(target=timer.main)
        t1.start()

    elif intent == 'StopWatch':
        t1 = Thread(target=stopwatch.main())


    else:
        speak('Command not found')
