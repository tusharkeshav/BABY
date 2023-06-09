import math
import webbrowser
import re
import search_engine_parser.core.exceptions
from search_engine_parser.core.engines.google import Search as GoogleSearch
from logs.Logging import log
from utilities import listening_animation
from utilities.internet import check_internet
from speech.text2speech import speak
from utilities.recognition import recognize

netflix_dork = '{movie} inurl:"netflix.com" inurl:"title"'
prime_dork = '{movie} inurl:"primevideo.com/detail"'


def _get_original_link(url: str) -> str:
    url_list = url.split('q=')
    log.debug(f'Netflix url retrieved from google is: {url}')
    return url_list[1]


def remove_special_characters(text: str) -> str:
    # Define the pattern to match special characters
    pattern = r'[^a-zA-Z0-9\s]'

    # Use the pattern to replace special characters with an empty string
    text = re.sub(pattern, '', text)

    return text


def confidence(query: str, search_result_title: str):
    title = remove_special_characters(search_result_title).lower().split(" ")
    query = query.lower().split(" ")
    confidence_count = 0
    for chunk in query:
        if chunk in title:
            confidence_count += 1
    if math.ceil(confidence_count / len(query)) * 100 >= 50:
        return True
    return False


def search_netflix(file: str):
    """
    It will try to search netflix movie list
    :param file: Sound file.
    :return: None
    """
    if not check_internet():
        speak('You are not connected to internet')
        return
    movie = recognize(file, filter_keywords=True)
    log.debug('Recognized movie is: {movie}'.format(movie=movie))
    if movie.replace(' ', '') == '':
        speak('Which movie are you looking for?')
        movie = listening_animation.get_data(calling_func='netflix')[0]
        if movie.replace(' ', '') == '':
            log.debug('Recognizer didn\'t give any results.')
            return
    try:
        result = GoogleSearch().search(query=netflix_dork.format(movie=movie), page=1)
        netflix_url = _get_original_link(result[0]['raw_urls'])
        if confidence(movie, result[0]['titles']):
            webbrowser.open(netflix_url)
            speak('Here is your search result')
        else:
            raise search_engine_parser.core.exceptions.NoResultsFound
    except search_engine_parser.core.exceptions.NoResultsFound as e:
        speak('No search results found for movie name {query} on netflix'.format(query=movie))
        log.debug('No search results were found for {query} on netflix'.format(query=movie))
    except Exception as e:
        log.exception(
            'Some unknown error occurred while searching for Netflix. Exception: {exception}'.format(exception=e))


def search_prime(file: str):
    if not check_internet():
        speak('You are not connected to internet')
        return
    movie = recognize(file, filter_keywords=True)
    log.debug('Recognized movie is: {movie}'.format(movie=movie))
    if movie.replace(' ', '') == '':
        speak('Which movie are you looking for?')
        movie = listening_animation.get_data(calling_func='prime')[0]
        if movie.replace(' ', '') == '':
            log.debug('Recognizer didn\'t give any results.')
            return
    try:
        result = GoogleSearch().search(query=prime_dork.format(movie=movie), page=1)
        prime_url = _get_original_link(result[0]['raw_urls'])
        webbrowser.open(prime_url)
        speak('Here is your search result')
    except search_engine_parser.core.exceptions.NoResultsFound as e:
        speak('No search results found for movie name {query} on amazon prime'.format(query=movie))
        log.debug('No search results were found for {query} on amazon prime'.format(query=movie))
    except Exception as e:
        log.exception(
            'Some unknown error occurred while searching for amazon prime. Exception: {exception}'.format(exception=e))

# search_google('your name inurl:"netflix.com"')
# search_netflix('vinchanzo inurl:"netflix.com" intitle:""')
