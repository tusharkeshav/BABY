import random
from voice2json import *


# Perform the coin flip
def flip():
    result = random.choice(["Heads", "Tails"])
    speak("It's is {state}".format(state=result))


# Display the result
print(flip())
