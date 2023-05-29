import os
import playsound as play

os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/../')


def playsound(path):
    play.playsound(path)
