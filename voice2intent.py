import json
import subprocess
# from log import log
import time
from concurrent.futures import ThreadPoolExecutor
from playsound import playsound

import change_brightness
import date_time
import media
import random_number
import stopwatch
import timer
import volume
import weather
from text2speech import speak

SUBMIT_JOB = ThreadPoolExecutor(max_workers=10)
RECORD_FILE = '/tmp/save.wav'


def run(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return output


def run_output(cmd):
    output = subprocess.getstatusoutput(cmd)
    return output


def record_analyse() -> list:
    """
    Record and feed to intent recognition.
    :return:
    """
    print('Recording voice')
    SUBMIT_JOB.submit(playsound, 'sounds/start.wav')
    time.sleep(0.5)
    # record = run('timeout 5 arecord -q -r 16000 -c 1 -f S16_LE -t wav /tmp/abc.wav')
    # voice2json = run('/usr/bin/voice2json transcribe-wav < /tmp/abc.wav | voice2json recognize-intent')
    voice2json = run_output(
        '/usr/bin/arecord -q -r 16000 -c 1 -f S16_LE -t raw | /usr/bin/voice2json transcribe-stream -c 1 '
        '-a - --wav-sink {wav_file} | /usr/bin/voice2json recognize-intent '.format(wav_file=RECORD_FILE))
    # print(voice2json[1].split('\n'))
    playsound('sounds/stop.wav')
    voice2json = json.loads(voice2json[1].split('\n')[7])
    print(f"Generated voice command: {voice2json}")
    if voice2json['text'] == '':
        return None, None

    intent = str(voice2json['intent']['name'])
    return intent, voice2json


def indentify_intent(force=True):
    """
    It will be used when its required for accuracy. For accuracy we will first send voice command
    to speech2text recognizer then from that analyzing intent. It ensure highest accuracy.
    :param force:
    :return: intent
    """
    import recognition
    query = recognition.recognize(RECORD_FILE, filter_keywords=False)
    intent = run_output(f'/usr/bin/voice2json recognize-intent --text-input {query}')


def voice_2_intent():
    """
    Action that will be performed. In other words, it mainitain all the skills
    :return:
    """
    from listening_animation import get_data
    # start()
    # print(f"we are found voice intent {gett()}")
    # return
    intent, voice2json = get_data()
    print(f'intent is {intent}')
    if intent is None:
        return
    if intent == 'Terminal':
        speak('Opening terminal')
        cmd = 'gnome-terminal'
        run(cmd)

    elif intent == 'Brightness':
        print(voice2json['slots'])
        if 'increase' in voice2json['slots']['action']:  # increase
            speak('Increasing Brightness')
            SUBMIT_JOB.submit(change_brightness.increase_brightness)
        elif 'decrease' in voice2json['slots']['action']:  # decrease
            SUBMIT_JOB.submit(change_brightness.decrease_brightness)
        elif 'brightness' in voice2json['slots']['action']:  # set
            value = str(voice2json['slots'].get('brightness', 0))
            speak('Changing bright Brightness to {value}'.format(value=value))
            print('Changing bright Brightness to {value}'.format(value=value))
            curr_brightness = change_brightness.get_brightness()
            print('value is {}'.format(value))
            if int(curr_brightness) > int(value):
                speak('Increasing brightness to {value}'.format(value=value))
            else:
                speak(f'Decreasing brightness to {value}'.format(value=value))
            SUBMIT_JOB.submit(change_brightness.increase_brightness, value)

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
        import coin_flip
        coin_flip.flip_coin()
        pass

    elif intent == 'RollDice':
        import roll_dice
        roll_dice.roll_dice()

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
        if 'action' in voice2json['slots']:
            if 'increase' in voice2json['slots']['action']:  # increase
                speak('Increasing Volume')
                SUBMIT_JOB.submit(volume.increase_volume())
            elif 'decrease' in voice2json['slots']['action']:  # decrease
                SUBMIT_JOB.submit(volume.decrease_volume())
        elif 'sound' in voice2json['slots']:  # set
            value = str(voice2json['slots'].get('sound', 0))
            speak('Changing sound to {value}'.format(value=value))
            print('Changing sound to {value}'.format(value=value))
            curr_sound = volume.get_volume()
            print('value is {}'.format(value))
            if int(curr_sound) > int(value):
                speak('Increasing sound to {value}'.format(value=value))
            else:
                speak('Decreasing sound to {value}'.format(value=value))
            SUBMIT_JOB.submit(volume.change_volume, value)
        pass
    elif intent == 'Bluetooth':
        import bluetooth_toggle
        if 'on' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(bluetooth_toggle.bluetooth_ON)
        elif 'off' in voice2json['slots']['action']:
            print('Turning off bluetooth')
            SUBMIT_JOB.submit(bluetooth_toggle.bluetooth_OFF)

    elif intent == 'SearchSong':
        if 'youtube' in voice2json['slots']['app']:
            import youtube
            SUBMIT_JOB.submit(youtube.search_song, RECORD_FILE)
        elif 'spotify' in voice2json['slots']['app']:
            import spotify
            SUBMIT_JOB.submit(spotify.search_song, RECORD_FILE)
            speak('Searching Spotify for you.')

    elif intent == 'SearchSpotify':
        import spotify
        SUBMIT_JOB.submit(spotify.search_song, RECORD_FILE)

    else:
        speak('Sorry I don\'t understand this. Can you please repeat')
