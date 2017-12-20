# By: Riasat Ullah

from pytz import timezone
import datetime

timezone_region = 'Africa/Nairobi'


def current_date():
    return datetime.datetime.now(
        timezone(timezone_region)).strftime('%Y%m%d')


def current_timestamp():
    return datetime.datetime.now(
        timezone(timezone_region)).strftime('%Y%m%d %H:%M:%S')


def date_with_delta(delta, base_date=None):
    if base_date is None:
        base_date = datetime.datetime.now(timezone(timezone_region))
    new_date = (base_date - datetime.timedelta(delta)).strftime('%Y%m%d')
    return new_date


def date_range(first_date, last_date):
    pattern = '%Y%m%d'
    first = datetime.datetime.strptime(first_date, pattern)
    last = datetime.datetime.strptime(last_date, pattern)
    if first > last:
        temp = last
        last = first
        first = temp
    diff = (last - first).days
    dates = []
    for i in range(0, diff+1):
        dates.append((first + datetime.timedelta(i)).strftime(pattern))
    return dates


def accrual_period(date1, date2):
    assert isinstance(date1, str)
    assert isinstance(date2, str)
    date1 = date1.replace('-', '')
    date2 = date2.replace('-', '')
    date1 = datetime.datetime.strptime(date1, '%Y%m%d')
    date2 = datetime.datetime.strptime(date2, '%Y%m%d')
    return (date2 - date1).days + 1


def string_to_date(string):
    '''
    Converts a string date in the format %Y%m%d to a datetime object
    :param string: string date
    :return: datetime object
    '''
    assert isinstance(string, str)
    return datetime.datetime.strptime(string, '%Y%m%d').date()


def date_to_string(date):
    '''
    Converts a datetime.datetime.date object to string
    :param date: datetime.datetime.date object
    :return: date as string
    '''
    return date.strftime('%Y%m%d')
