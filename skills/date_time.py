from datetime import datetime
from calendar import month_name

from speech.text2speech import speak
from logs.Logging import log


def get_date():
    date = datetime.now().strftime('%d %m %Y')
    date = date.split(' ')
    speak('The date is {day} {month} {year}'.format(day=date[0], month=month_name[int(date[1])], year=date[2]))
    log.debug(f'The date is: {date}')
    pass


def get_time():
    time = datetime.now().strftime('%I %M %p').split(' ')
    speak('The time is {hour} {minute} {noon}'.format(hour=int(time[0]), minute=time[1], noon=time[2]))
    log.debug(f'The time is: {time}')
    pass
