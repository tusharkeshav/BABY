import random
from voice2json import *


def dice_roll():
    dice_roll = random.randint(1, 6)
    speak("You got {dice_roll}".format(dice_roll=dice_roll))
