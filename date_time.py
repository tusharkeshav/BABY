from datetime import datetime
from calendar import month_name

from text2speech import speak


def get_date():
    date = datetime.now().strftime('%d %m %Y')
    date = date.split(' ')
    speak('The date is {day} {month} {year}'.format(day=date[0], month=month_name[int(date[1])], year=date[2]))
    pass


def get_time():
    time = datetime.now().strftime('%I %M %p').split(' ')
    speak('The time is {hour} {minute} {noon}'.format(hour=int(time[0]), minute=time[1], noon=time[2]))
    pass
