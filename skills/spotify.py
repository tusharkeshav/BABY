import json
import time

import spotipy
import webbrowser
import utilities.recognition as recognition, utilities.record as record
from speech.text2speech import speak
import configparser as cp

from logs.Logging import log

config = cp.ConfigParser()
config.optionxform = str
config.read('config.ini')


class Spotify_Client_Secret_Missing:
    pass


clientID = str(config['spotify']['clientID'])
clientSecret = str(config.get('spotify', 'clientSecret'))
if None in (clientID, clientSecret) or '' in (clientID, clientSecret):
    raise Spotify_Client_Secret_Missing()
redirect_uri = 'http://google.com/callback/'
oauth_object = spotipy.SpotifyOAuth(clientID, clientSecret, redirect_uri)
token_dict = oauth_object.get_access_token()
token = token_dict['access_token']
spotifyObject = spotipy.Spotify(auth=token)
user_name = spotifyObject.current_user()

# To print the JSON response from
# browser in a readable format.
# optional can be removed
print(json.dumps(user_name, sort_keys=True, indent=4))


def _launch_spotify(search_song):
    # while True:
    #     print("Welcome to the project, " + user_name['display_name'])
    #     print("0 - Exit the console")
    #     print("1 - Search for a Song")
    #     user_input = int(input("Enter Your Choice: "))
    #     if user_input == 1:
    #         search_song = input("Enter the song name: ")
    #         results = spotifyObject.search(search_song, 1, 0, "track")
    #         songs_dict = results['tracks']
    #         song_items = songs_dict['items']
    #         song = song_items[0]['external_urls']['spotify']
    #         webbrowser.open(song)
    #         print('Song has opened in your browser.')
    #     elif user_input == 0:
    #         print("Good Bye, Have a great day!")
    #         break
    #     else:
    #         print("Please enter valid user-input.")
    results = spotifyObject.search(search_song, 1, 0, "track")
    songs_dict = results['tracks']
    song_items = songs_dict['items']
    song = song_items[0]['external_urls']['spotify']
    webbrowser.open(song)
    log.debug('Song has opened in your browser.')


def search_song(file):
    song = recognition.recognize(file, filter_keywords=True)
    if song is '':
        log.debug('Recognizer didn\'t give song result.')
        speak('What song you would like to listen?')
        time.sleep(0.5)
        song = record.record_and_analyse()
        if song.replace(' ', '') == '':
            log.debug('Song was not identified by recognizer. Returning simply.')
            return
    _launch_spotify(song)
    speak('Here is your searched song')
    pass
