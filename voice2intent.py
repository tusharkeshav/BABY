import json
import subprocess
import os
from logs.Logging import log
import time
from concurrent.futures import ThreadPoolExecutor
from sounds.play import playsound

from skills import change_brightness, media, volume, date_time, random_number, weather, stopwatch, timer, phone
from speech.text2speech import speak

SUBMIT_JOB = ThreadPoolExecutor(max_workers=10)
RECORD_FILE = '/tmp/save.wav'
os.chdir(os.path.dirname(os.path.abspath(__file__)))


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
    log.info('Recording voice')
    SUBMIT_JOB.submit(playsound, 'sounds/start.wav')
    time.sleep(0.5)
    # record = run('timeout 5 arecord -q -r 16000 -c 1 -f S16_LE -t wav /tmp/abc.wav')
    # voice2json = run('/usr/bin/voice2json transcribe-wav < /tmp/abc.wav | voice2json recognize-intent')
    voice2json = run_output(
        '/usr/bin/arecord -q -r 16000 -c 1 -f S16_LE -t raw | /usr/bin/voice2json transcribe-stream -c 1 '
        '-a - --wav-sink {wav_file} | /usr/bin/voice2json recognize-intent '.format(wav_file=RECORD_FILE))
    # log.info(voice2json[1].split('\n'))
    playsound('sounds/stop.wav')
    voice2json = json.loads(voice2json[1].split('\n')[7])
    log.info(f"Generated voice command: {voice2json}")
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
    import utilities.recognition as recognition
    query = recognition.recognize(RECORD_FILE, filter_keywords=False)
    intent = run_output(f'/usr/bin/voice2json recognize-intent --text-input {query}')


def voice_2_intent():
    """
    Action that will be performed. In other words, it mainitain all the skills
    :return:
    """
    from utilities.listening_animation import get_data

    intent, voice2json = get_data(calling_func='voice2intent')
    log.info(f'intent is {intent}')
    if intent is None:
        return
    if intent == 'Terminal':
        speak('Opening terminal')
        cmd = 'gnome-terminal'
        run(cmd)

    elif intent == 'Brightness':
        log.info(voice2json['slots'])
        if 'action' in voice2json['slots']:  # increase
            if 'increase' in voice2json['slots']['action']:
                speak('Increasing Brightness')
                SUBMIT_JOB.submit(change_brightness.increase_brightness)
            elif 'decrease' in voice2json['slots']['action']:  # decrease
                SUBMIT_JOB.submit(change_brightness.decrease_brightness)
        elif 'brightness' in voice2json['slots']:  # set
            value = str(voice2json['slots'].get('brightness', 0))
            speak('Changing bright Brightness to {value}'.format(value=value))
            log.info('Changing bright Brightness to {value}'.format(value=value))
            curr_brightness = change_brightness.get_brightness()
            log.info('value is {}'.format(value))
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
        from skills import coin_flip
        coin_flip.flip_coin()
        pass

    elif intent == 'RollDice':
        from skills import roll_dice
        roll_dice.roll_dice()

    elif intent == 'Media':
        log.info('Found Media intent')
        value = str(voice2json['slots'].get('status', 0))
        log.info(value)
        if value in ('resume', 'pause', 'stop', 'play'):
            log.info("Media intent value is {}".format(value))
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
            # speak('Changing sound to {value}'.format(value=value))
            log.info('Changing sound to {value}'.format(value=value))
            curr_sound = volume.get_volume()
            log.info('Volume intent value is {}'.format(value))
            if int(curr_sound) > int(value):
                speak('Increasing sound to {value}'.format(value=value))
            else:
                speak('Decreasing sound to {value}'.format(value=value))
            SUBMIT_JOB.submit(volume.change_volume, value)
        pass
    elif intent == 'Bluetooth':
        from skills import bluetooth_toggle
        if 'on' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(bluetooth_toggle.bluetooth_ON)
        elif 'off' in voice2json['slots']['action']:
            log.info('Turning off bluetooth')
            SUBMIT_JOB.submit(bluetooth_toggle.bluetooth_OFF)

    elif intent == 'SearchSong':
        # NOTE: We wont submit the function in threadpool. Since, we are using animationa and PYQT dont support
        # runnning expect main thread. So submitting job in main function only.
        if 'youtube' in voice2json['slots']['app']:
            from skills import youtube
            youtube.search_song(RECORD_FILE)
            # SUBMIT_JOB.submit(youtube.search_song, RECORD_FILE)
        elif 'spotify' in voice2json['slots']['app']:
            from skills import spotify
            spotify.search_song(RECORD_FILE)
            # SUBMIT_JOB.submit(spotify.search_song, RECORD_FILE)
            SUBMIT_JOB.submit(speak, 'Searching Spotify.')

    elif intent == 'SearchMovie':
        from skills import search_movie
        if 'netflix' in voice2json['slots']['app']:
            SUBMIT_JOB.submit(speak, "Searching netflix")
            search_movie.search_netflix(RECORD_FILE)
        elif 'prime' in voice2json['slots']['app']:
            SUBMIT_JOB.submit(speak, "Searching prime videos")
            search_movie.search_prime(RECORD_FILE)

    elif intent == 'SearchSpotify':
        from skills import spotify
        SUBMIT_JOB.submit(spotify.search_song, RECORD_FILE)

    elif intent == 'Phone':
        if 'ring' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(phone.ring_device)
            pass
        elif 'ping' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(phone.ping_device)
            pass

    else:
        speak('Sorry I don\'t understand this. Can you please repeat')
