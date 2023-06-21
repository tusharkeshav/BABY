import subprocess
import utilities.recognition as recognition
from config.get_config import get_config

FILE = '/tmp/record.wav'
TIMEOUT = 4  # Timeout is the duration for which you wanted to record for
ARECORD = get_config('default', 'arecord')


def run() -> None:
    subprocess.getstatusoutput('{arecord} -q -r 16000 -d {timeout} -c 1 -f S16_LE -t wav {save_path}'.format(save_path=FILE, timeout=TIMEOUT, arecord=ARECORD))


def record() -> None:
    """
    Record audio and save it to default path:/tmp/record.wav
    :return:
    """
    run()
    pass


def record_and_analyse() -> str:
    """
    Record sound and analyse it via recogniser
    :return: analyzed words/query
    """
    run()
    analyzed_words = recognition.recognize(file=FILE, filter_keywords=False)
    return analyzed_words
