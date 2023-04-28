import random
from voice2intent import *


# Perform the coin flip
def flip_coin():
    result = random.choice(["Heads", "Tails"])
    speak("It's is {state}".format(state=result))

