import time
import webbrowser

from utilities.recognition import recognize
from speech.text2speech import speak
from utilities.internet import check_internet
from utilities import listening_animation
from logs.Logging import log


def search_song(file):
    song = recognize(file, filter_keywords=True) if check_internet() else speak(
        "I am finding difficulty while connecting to Internet")
    if check_internet():
        song = recognize(file, filter_keywords=True)
        log.debug('Recognized song keywords: {song}'.format(song=song))
        if song.replace(' ', '') == '':  # removing spaces
            log.debug('Recognizer didn\'t give song result.')
            speak('What song you would like to search for?')
            time.sleep(0.2)
            song = listening_animation.get_data(calling_func='youtube')[0]
            if song.replace(' ', '') == '':
                log.debug('Song was identified by recognizer. Returning simply.')
                return

    webbrowser.open('https://www.youtube.com/results?search_query={search}'.format(search=song))
    speak('Here are the search results')
