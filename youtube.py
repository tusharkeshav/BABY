import webbrowser

from recognition import recognize
from text2speech import speak
from internet import check_internet


def search_song(file):
    song = recognize(file, filter_keywords=True) if check_internet() else speak("I am finding difficulty while connecting to Internet")
    webbrowser.open('https://www.youtube.com/results?search_query={search}'.format(search=song))
    speak('Here are the search results')
