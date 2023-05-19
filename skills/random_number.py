import random
from speech.text2speech import speak


def get_random_number():
    number = random.randint(0, 100000000)
    speak('Random number generated is {}'.format(number))
