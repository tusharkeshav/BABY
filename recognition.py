import speech_recognition as sr
import webbrowser
from text2speech import speak
from internet import check_internet

keyword_delete = ['find', 'play', 'youtube', 'music', 'search song on', 'search song', 'search']


def recognize(file):
    r = sr.Recognizer()
    audio_data = sr.AudioFile(file)

    with audio_data as source:
        print('reading data')
        audio = r.record(source)
        r.pause_threshold = 1

    try:
        print('recognizing data')
        query = str(r.recognize_google(audio)).lower()
        query = str('search song on YouTube Naino wale Ne Cheda Man Ka Pyala').lower()
        for word in keyword_delete:
            query = query.replace(word, '')
        print(query)
        webbrowser.open('https://www.youtube.com/results?search_query={search}'.format(search=query))
        speak('Following are the search results.')
    except Exception as e:
        print(f"Exception while recognizing text. Exception: {e}")


def search_youtube(file):
    recognize(file) if check_internet() else speak("I am finding difficulty while connecting to Internet")
