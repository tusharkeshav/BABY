import requests
from speech.text2speech import speak
from logs.Logging import log

def _hit_api(api):
    try:
        response = requests.get(url=api, timeout=3)
        if response.status_code == 200:
            return response.json()
        else:
            speak('Some issue while finding weather result.')
    except Exception as e:
        log.error('Issue occurred while executing {api}. Exception occurred: {e}'.format(api=api, e=e))


def _check_ip():
    api = 'https://api-bdc.net/data/client-ip'
    response = _hit_api(api)
    ip = response['ipString']
    return ip


def _get_lat_long(ip: str):
    api = 'http://ip-api.com/json/{}'.format(ip)
    response = _hit_api(api)
    if response['status'].lower() == 'success':
        return response['lat'], response['lon']
    elif response['status'].lower() == 'failed' or response == None:
        return 0, 0


def get_weather():
    latitude, longitude = _get_lat_long(_check_ip())
    api = 'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&' \
          'daily=temperature_2m_max,temperature_2m_min,showers_sum&' \
          'forecast_days=1&timezone=auto'.format(latitude=latitude, longitude=longitude)
    response = _hit_api(api)
    print(response)
    minimum_temp = response['daily']['temperature_2m_min'][0]
    maximum_temp = response['daily']['temperature_2m_max'][0]
    msg1 = 'It is going to be shiny day with'
    if response['daily']['showers_sum'] == 1:
        msg1 = 'It is going to be rainy day with'

    speak(msg1 + 'Maximum temperature would be {max} degree celsius and '
                 'minium temperature would be {min} degree celsius'.format(max=maximum_temp, min=minimum_temp))


def get_rain_snow():
    latitude, longitude = _get_lat_long(_check_ip())
    api = 'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&' \
          'daily=rain_sum,showers_sum,snowfall_sum&forecast_days=1&' \
          'timezone=auto'.format(latitude=latitude, longitude=longitude)
    response = _hit_api(api)
    msg1 = ''
    msg2 = ''
    check = True
    if response['daily']['rain_sum'] == 1:
        msg1 = 'It is going to rain today'
        check = False
    if response['daily']['snowfall_sum'] == 1:
        msg2 = 'It is going to be snowfall today'
        check = False
    if check:
        speak('It is sunny day')

    speak(msg1 + msg2)
