import os
import subprocess
from logs.Logging import log
from config.get_config import get_config

method: str = get_config('speech', 'method')  # Which method to use.
PLAY = get_config('default', 'play')


def speak(text) -> None:
    """
    Module to convert text to speech. Convert realtime pass string to speech
    :param text: String to be converted to speech
    :return: None
    """
    output = ''
    error = ''
    try:
        # subprocess.getoutput('espeak "{text}"'.format(text=text)) subprocess.getoutput("/usr/bin/festival -b '(
        # voice_cmu_us_slt_arctic_hts)' '(SayText \"{text}\")'".format(text=text))


        # NOTE: /bin/bash -c set -o pipefall
        # command is addded to enforce and give status as 0. If we don't use it and in somecase pipe command fail
        # then it wont give non zero status. Using this command it ensure that it will give non sero status if
        # command filed
        if method.lower() == 'pico2wave':
            output = subprocess.run(["/bin/bash", "-c",
                                     "set -o pipefail; export t='abc.wav'; pico2wave -l en-US -w $t \"{text}\"; aplay "
                                     "$t ; rm $t".format(
                                         text=text)])
        elif method.lower() == 'piper':
            output = subprocess.run(["/bin/bash", "-c", "set -o pipefail; echo \"{text}\" | {path}piper --model {"
                                                        "path}models/{model} --output_raw | {play} -t raw -r 16000 "
                                                        "--bits 16 -e signed-integer -".format(text=text,
                                                                                               model=get_config('speech', 'piper_model'),
                                                                                               path='speech/piper/', play=PLAY)],
                                                                                                stderr=subprocess.PIPE,)
        if output.returncode != 0:
            error = output.stderr.decode('utf-8')
            raise RuntimeError('Subprocess failed to execute command')
    except Exception as e:
        log.exception(
            'Exception while converting text to speech. Exception: {exception} Error: {error}'.format(exception=e,
                                                                                                      error=error))
        print('Exception while converting text to speech. Exception: {exception} Error: {error}'.format(exception=e,
                                                                                                        error=error))
