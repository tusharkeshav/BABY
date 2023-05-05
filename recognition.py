import speech_recognition as sr

keyword_delete = ['find', 'play', 'youtube', 'music', 'search song on', 'search song', 'search', 'song on', 'spotify']


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
        print('reading data')
        audio = r.record(source)
        r.pause_threshold = 1

    try:
        print('recognizing data')
        query = str(r.recognize_google(audio)).lower()
        query = str('search song on YouTube Naino wale Ne Cheda Man Ka Pyala').lower()
        if filter_keywords:
            for word in keyword_delete:
                query = query.replace(word, '')
        print(query)
        return query
    except Exception as e:
        print(f"Exception while recognizing text. Exception: {e}")
