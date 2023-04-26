import subprocess


def speak(text):
    try:
        subprocess.getoutput('espeak "{text}"'.format(text=text))

    except Exception as e:
        print('Exception while converting text to speech. Exception: {exception}'.format(exception=e))
