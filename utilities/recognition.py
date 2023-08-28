import speech_recognition as sr
from logs.Logging import log

keyword_delete = ['find', 'play', 'youtube', 'music', 'search song on', 'search song', 'search', 'song on', 'spotify'
                  'movie', 'movie on', 'movie in', 'netflix', 'search movie', 'spotify', 'video', 'sad']


def _clean_query(query: str, filter_keywords: bool) -> str:

    # Filter keywords
    if filter_keywords:
        for word in keyword_delete:
            query = query.replace(word, '')

    # remove trailing and leading spaces if any
    query = ' '.join(query.split())
    return query


def recognize(file, filter_keywords):
    """
    Recognize the input file(audio) and convert it to text
    :param file: audion file. Default location is /tmp/save.wav
    :param filter_keywords: If you require to filter some keywords from the resultant speech. its is required to search song on youtube etc
    :return: text translation of speech
    """
    r = sr.Recognizer()
    audio_data = sr.AudioFile(file)

    with audio_data as source:
        log.debug('*********** started reading data **************')
        audio = r.record(source)
        r.pause_threshold = 1

    try:
        print('*********** started recognizing data **************')
        log.debug('*********** started recognizing data **************')
        query = str(r.recognize_google(audio)).lower()
        log.debug(f'Recognized query before filtering is: {query}')
        query = _clean_query(query, filter_keywords)
        log.debug(f'Recognized query after filtering is: {query}')
        return query
    except Exception as e:
        log.error(f"Exception while recognizing text. Exception: {e}")
        return ''
