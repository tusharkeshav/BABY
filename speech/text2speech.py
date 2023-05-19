import subprocess
from logs.Logging import log


def speak(text):
    try:
        # subprocess.getoutput('espeak "{text}"'.format(text=text))
        # subprocess.getoutput("/usr/bin/festival -b '(voice_cmu_us_slt_arctic_hts)' '(SayText \"{text}\")'".format(text=text))
        subprocess.getoutput(
            "export t='abc.wav'; pico2wave -l en-US -w $t \"{text}\"; aplay $t ; rm $t".format(text=text))

    except Exception as e:
        log.errr('Exception while converting text to speech. Exception: {exception}'.format(exception=e))
        print('Exception while converting text to speech. Exception: {exception}'.format(exception=e))
