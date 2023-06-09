import math
import time
import webbrowser
import re
from utilities.recognition import recognize
from speech.text2speech import speak
from utilities.internet import check_internet
from utilities import listening_animation
from logs.Logging import log
import pytube as YouTube

COUNT = 2  # check for top two result in youtube search


def remove_special_characters(text: str) -> str:
    # Define the pattern to match special characters
    pattern = r'[^a-zA-Z0-9\s]'

    # Use the pattern to replace special characters with an empty string
    text = re.sub(pattern, '', text)

    return text


def confidence(query: str):
    """
    This will calculate the confidence of the youtube search result vs input and judge if 1st result is exactly what user is asking for.
    This is required to fetch the exact youtube video or say watch url, if the video is exact match then lets return video to user.
    :return: direct link to video based on confidence score
    """
    results = YouTube.Search('query').results
    query_chunks = query.lower().split(' ')
    confidence_count = 0
    tmp = COUNT
    if len(results) != 0:
        for result in results:
            title = remove_special_characters(str(result.title).lower())
            title = title.split(' ')
            for chunk in query_chunks:
                if chunk in title:
                    confidence_count += 1

            if math.ceil(confidence_count / len(query_chunks)) * 100 >= 50:
                """this is confidence formula = (Number of word found)/(total words that were checked) * 100"""
                return result.watch_url

            tmp -= 1
            if tmp <= 0:    break
    return None


def search_song(file):
    if not check_internet():
        speak('Looks like you are not connected to internet.')
        return
    song = recognize(file, filter_keywords=True)
    if song == '':
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
    direct_yt_link = confidence(song)
    if direct_yt_link is not None:
        webbrowser.open(direct_yt_link)
    else:
        webbrowser.open('https://www.youtube.com/results?search_query={search}'.format(search=song))
    speak('Here are the search results')
