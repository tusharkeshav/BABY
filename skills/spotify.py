import json
import math
import re
import time
from urllib.parse import unquote

import search_engine_parser.core.exceptions
import spotipy
import webbrowser
from search_engine_parser.core.engines.duckduckgo import Search as DuckDuckGo
import utilities.recognition as recognition, utilities.listening_animation as listening_animation
from speech.text2speech import speak
import configparser as cp

from logs.Logging import log
from utilities.internet import check_internet
from config.get_config import get_config

config = cp.ConfigParser()
config.optionxform = str
config.read('config.ini')
method = get_config('spotify', 'method', 'dork')
filter_keywords = ['spotify']


class SpotifyClientSecretMissing(Exception):
    pass


def _launch_spotify(search_song):
    clientID = str(config['spotify']['clientID'])
    clientSecret = str(config.get('spotify', 'clientSecret'))
    if None in (clientID, clientSecret) or '' in (clientID, clientSecret):
        raise SpotifyClientSecretMissing()
    redirect_uri = 'http://google.com/callback/'
    oauth_object = spotipy.SpotifyOAuth(clientID, clientSecret, redirect_uri)
    token_dict = oauth_object.get_access_token()
    token = token_dict['access_token']
    spotifyObject = spotipy.Spotify(auth=token)
    user_name = spotifyObject.current_user()
    log.debug(json.dumps(user_name, sort_keys=True, indent=4))
    results = spotifyObject.search(search_song, 1, 0, "track")
    songs_dict = results['tracks']
    song_items = songs_dict['items']
    song = song_items[0]['external_urls']['spotify']
    webbrowser.open(song)
    log.debug('Song has opened in your browser.')


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
        match = re.search(r'uddg=(.*?)&rut', url)
        if match:
            url_extracted = match.group(1)
            log.debug(f'DuckDuckGo extracted link: {url_extracted}')
            return unquote(url_extracted)
        return url


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


def spotify_dork_search(song):
    spotify_dork = '{song} site:spotify.com'

    try:
        log.debug('Search query on spotify: {query}'.format(query=spotify_dork.format(song=song)))
        result = DuckDuckGo().search(query=spotify_dork.format(song=song), page=1)
        log.debug(f'Result for spotify from duckduckgo {result[0]}')
        spotify_url = _get_original_link(result[0]['links'], engine='duckduckgo')
        if confidence(song, result[0]['titles'], filter_keywords=filter_keywords):
            webbrowser.open(spotify_url)
            speak('Here is your searched song')
        else:
            raise search_engine_parser.core.exceptions.NoResultsFound
    except (search_engine_parser.core.exceptions.NoResultsFound, IndexError) as e:
        speak('No search results found for movie name {query} on spotify'.format(query=song))
        log.debug('No search results were found for {query} on spotify'.format(query=song))
    except Exception as e:
        speak('Some error occurred while searching spotify.')
        log.exception(
            'Some unknown error occurred while searching for Spotify. Exception: {exception}'.format(exception=e))


def search_song(file):
    if not check_internet():
        speak('Looks like you are not connected to internet.')
        return
    song = recognition.recognize(file, filter_keywords=True)
    if song.replace(' ', '') == '':
        log.debug('Recognizer didn\'t give song result.')
        speak('What song you would like to listen?')
        time.sleep(0.2)
        song = listening_animation.get_data(calling_func='spotify')[0]
        if song.replace(' ', '') == '':
            log.debug('Song was not identified by recognizer. Returning simply.')
            return
    if method == 'dork':
        spotify_dork_search(song)
        pass
    elif method == 'spotipy':
        _launch_spotify(song)
