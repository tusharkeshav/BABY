import subprocess

MUTE = 0
LOWER = 20
temp = 20


def _set_volume(volume):
    subprocess.getoutput('amixer set Master {volume}%'.format(volume=volume))


def change_volume(volume):
    _set_volume(volume)


def lower_volume():
    _set_volume(LOWER)


def raise_volume_to_normal(original_volume):
    '''Can be to decrease voice and again raise voice,
    if there is some song/audio running
    '''
    _set_volume(original_volume)


def mute():
    _set_volume(MUTE)
