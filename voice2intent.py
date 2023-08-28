import json
import re
import subprocess
import os
from logs.Logging import log
import time
from concurrent.futures import ThreadPoolExecutor
from sounds.play import playsound

from skills import change_brightness, media, volume, date_time, random_number, weather, stopwatch, timer, phone
from speech.text2speech import speak
from utilities.custom_skill import load_custom_skill, check_intent_exist_csv
from utilities.custom_skill_gui import add_skill
from config.get_config import get_config
from utilities.pre_checks import pre_checks
from utilities.similar_image_display import display_result

SUBMIT_JOB = ThreadPoolExecutor(max_workers=10)
RECORD_FILE = get_config('default', 'record_file')
VOICE2JSON = get_config('default', 'voice2json')
ARECORD = get_config('default', 'arecord')
# CONFIDENCE can range from 0.0 to 1.0
CONFIDENCE = float(get_config('default', 'confidence'))
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def run(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    return output


def run_output(cmd):
    output = subprocess.getstatusoutput(cmd)
    return output


def record_analyse() -> tuple:
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
        '{arecord} -q -r 16000 -c 1 -f S16_LE -t raw | {voice2json} transcribe-stream -c 1 '
        '-a - --wav-sink {wav_file} | /usr/bin/voice2json recognize-intent '.format(wav_file=RECORD_FILE, voice2json=VOICE2JSON, arecord=ARECORD))
    log.debug('Voice2json raw output: {}'.format(voice2json))
    playsound('sounds/stop.wav')

    # TODO:-> This is causing error. It's noticed that the value at 7 index is not always correct. Voice2json is
    #  giving output some randomly. IMPROVE IT
    # # voice2json = json.loads(voice2json[1].split('\n')[7])
    # voice2json = json.loads(voice2json[1].split('\n')[-1])

    # Finding the json value using regex instead of relying on splitting string and finding index
    json_pattern = r'\{.*\}'
    json_extract = re.search(pattern=json_pattern, string=voice2json[1]).group()
    voice2json = json.loads(json_extract)
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
    pre_checks()
    from utilities.listening_animation import get_data

    intent, voice2json = get_data(calling_func='voice2intent')
    log.info(f'intent is {intent}')
    if intent is None:
        return
    if float(voice2json['likelihood']) == CONFIDENCE:
        no_result()
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
                speak('Decreasing Brightness')
                SUBMIT_JOB.submit(change_brightness.decrease_brightness)
        elif 'brightness' in voice2json['slots']:  # set
            # Note we have to use default value (0) in below variable.
            # the issue is with voice2json. Its not converting 0. it passed empty when 0 is said
            value = str(voice2json['slots'].get('brightness', 0)) or 0
            log.info('Changing bright Brightness to {value}'.format(value=value))
            SUBMIT_JOB.submit(change_brightness.set_brightness, int(value))

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
        likelihood = float(voice2json['likelihood'])
        if likelihood < 0.7:
            no_result()
            return
        hours = '00'
        mins = '00'
        seconds = '00'
        msg_hr = msg_min = msg_sec = ''
        time_format = '{hours}:{mins}:{seconds}'
        if 'hours' in voice2json['slots']:
            hours = voice2json['slots']['hours']
            msg_hr = '{} hours'.format(hours)
            pass
        if 'mins' in voice2json['slots']:
            mins = voice2json['slots']['mins']
            msg_min = '{} minutes'.format(mins)
            pass
        if 'seconds' in voice2json['slots']:
            seconds = voice2json['slots']['seconds']
            msg_sec = '{} seconds'.format(seconds)
        time_format = time_format.format(hours=hours, mins=mins, seconds=seconds)
        if any([len(msg_hr) != 0, len(msg_min) != 0, len(msg_hr) != 0]):
            speak('Setting timer for {hr} {min} {sec}'.format(hr=msg_hr, min=msg_min, sec=msg_sec))
        else:
            speak('Launching timer. Please select the time.')
        SUBMIT_JOB.submit(timer.main, time_format)

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
            speak(f'Sure. {value} video')
            SUBMIT_JOB.submit(media.pause_resume_toggle)
        elif value == 'mute':
            speak('Sure. Muting the sound')
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
            curr_sound = volume.get_volume()
            log.debug(f'Current sound level: {curr_sound} and User input volume: {value}')
            if int(curr_sound) < int(value):
                speak('Increasing volume to {value}'.format(value=value))
            else:
                speak('Decreasing volume to {value}'.format(value=value))
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
            SUBMIT_JOB.submit(speak, 'Searching Spotify.')
            spotify.search_song(RECORD_FILE)
            # SUBMIT_JOB.submit(spotify.search_song, RECORD_FILE)

    elif intent == 'SearchMovie':
        from skills import search_movie
        if 'netflix' in voice2json['slots']['app']:
            SUBMIT_JOB.submit(speak, "Searching netflix")
            search_movie.search_netflix(RECORD_FILE)
        elif 'prime' in voice2json['slots']['app']:
            SUBMIT_JOB.submit(speak, "Searching prime videos")
            search_movie.search_prime(RECORD_FILE)

    elif intent == 'Phone':
        if 'ring' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(phone.ring_device)
            pass
        elif 'ping' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(phone.ping_device)
            pass
        elif 'send' in voice2json['slots']['action']:
            SUBMIT_JOB.submit(phone.send_clipboard)

    elif intent == 'Skill':
        add_skill()

    elif check_intent_exist_csv(intent=intent):
        SUBMIT_JOB.submit(load_custom_skill, intent)

    elif intent == 'SearchImage':
        from skills import search_similar_images
        if 'detect' in voice2json['slots']['action']:
            search_similar_images.get_image_header()
            pass
        elif 'similar' in voice2json['slots']['action']:
            result = search_similar_images.get_all_image_info()
            display_result(result)
            pass
        elif 'buy' in voice2json['slots']['action']:
            search_similar_images.get_buy_link_if_any()
            pass

    else:
        no_result()


def no_result():
    speak('Sorry I don\'t understand this. Can you please repeat')