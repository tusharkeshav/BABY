import math
import webbrowser
import re
from urllib.parse import unquote
import search_engine_parser.core.exceptions
from search_engine_parser.core.engines.google import Search as GoogleSearch
from search_engine_parser.core.engines.duckduckgo import Search as DuckDuckGo
from logs.Logging import log
from utilities import listening_animation
from utilities.internet import check_internet
from speech.text2speech import speak
from utilities.recognition import recognize

netflix_dork = '{movie} site:netflix.com'
prime_dork = '{movie} site:primevideo.com/detail'

netflix_keywords = ['offical', 'watch', 'netflix', 'site']
prime_keywords = ['prime', 'video', 'amazon']


def _get_original_link(url: str, engine: str) -> str:
    if engine == 'google':
        url_list = url.split('q=')
        log.debug(f'Netflix url retrieved from google is: {url}')
        return url_list[1]
    elif engine == 'duckduckgo':
        """
        Bug: There is a bug in duckduckgo response. it send sometime exact link to website or sometime starting with //:duckduckgo.com/blabla
        So, we are splitting url and picking the last index.
        """
        url_list = url.split('uddg=')
        log.debug(f'Duckduckgo url is {url} and split url: {url_list}')
        return unquote(url_list[-1])


def remove_special_characters(text: str) -> str:
    # Define the pattern to match special characters
    pattern = r'[^a-zA-Z0-9\s]'

    # Use the pattern to replace special characters with an empty string
    text = re.sub(pattern, ' ', text)
    text = ' '.join(text.split())

    return text


def confidence(query: str, search_result_title: str, filter_keywords: list):
    """
    Confidence score tell how confidence is the search result and the asked query. It find confidence between user
    asked query and the title return by search engine. it return bool which show True as confidence and false as not confident

    :formula: (Number of keyword in title(after cleaning) found in query) / (total title words) * 100
    :param query: User asked query
    :param search_result_title: Title of first searched result on search engine
    :param filter_keywords: Filter some keyword from the title.
    E.g: Netflix title is always: "Watch <movie-name> | Netflix official site". They keywords s.a netflix, watch,
    official, site can disturb confidence score
    :return: bool
    """
    title = remove_special_characters(search_result_title).lower()  # spiderman
    query = remove_special_characters(query).lower()  # spider man
    log.debug(f"Title: {title} and the searched query: {query}")
    confidence_count = 0
    if len(title) <= len(query):
        title = title.split()
        for chunk in title:
            if chunk not in filter_keywords and chunk in query:
                confidence_count += 1
        log.debug(f'Confidence count: {confidence_count}')
        if math.ceil(confidence_count / len(title)) * 100 >= 50:
            return True
    else:
        query = query.split()
        for chunk in query:
            if chunk in title:
                confidence_count += 1
        log.debug(f'Confidence count: {confidence_count}')
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
        log.debug('Searched query on netflix: {query}'.format(query=netflix_dork.format(movie=movie)))
        result = DuckDuckGo().search(query=netflix_dork.format(movie=movie), page=1)
        # netflix_url = _get_original_link(result[0]['raw_urls'], engine='google')
        log.debug(f'Result for netflex from duckduckgo {result[0]}')
        netflix_url = _get_original_link(result[0]['links'], engine='duckduckgo')
        if confidence(movie, result[0]['titles'], filter_keywords=netflix_keywords):
            webbrowser.open(netflix_url)
            speak('Here is your search result')
        else:
            raise search_engine_parser.core.exceptions.NoResultsFound
    except (search_engine_parser.core.exceptions.NoResultsFound, IndexError) as e:
        speak('No search results found for movie name {query} on netflix'.format(query=movie))
        log.debug('No search results were found for {query} on netflix'.format(query=movie))
    except Exception as e:
        speak('Some error occurred while searching netflix.')
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
        log.debug('Searched query on prime: {query}'.format(query=netflix_dork.format(movie=movie)))
        result = DuckDuckGo().search(query=prime_dork.format(movie=movie), page=1)
        # prime_url = _get_original_link(result[0]['raw_urls'], engine='google')
        prime_url = _get_original_link(result[0]['links'], engine='duckduckgo')
        if confidence(movie, result[0]['titles'], filter_keywords=prime_keywords):
            webbrowser.open(prime_url)
            speak('Here is your search result')
        else:
            raise search_engine_parser.core.exceptions.NoResultsFound
    except (search_engine_parser.core.exceptions.NoResultsFound, IndexError) as e:
        speak('No search results found for movie name {query} on amazon prime'.format(query=movie))
        log.debug('No search results were found for {query} on amazon prime'.format(query=movie))
    except Exception as e:
        speak('Some error occurred while searching amazon prime.')
        log.exception(
            'Some unknown error occurred while searching for amazon prime. Exception: {exception}'.format(exception=e))

# search_google('your name inurl:"netflix.com"')
# search_netflix('vinchanzo inurl:"netflix.com" intitle:""')
