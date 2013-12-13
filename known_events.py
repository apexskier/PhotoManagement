import re, calendar
from datetime import datetime, timedelta, date

weekdays = list(calendar.day_abbr)

# Add your own holidays here. I keep mine down to the ones that I might
# actually use, so I don't get ones added I don't need.
#
# Formats for keys, by example:
#   22-7 = 22nd of July
#   2Wed-8 = The second Wednesday of August
#
# Formats for values:
#   Specify a string to be used for the name of the event.
#     or
#   Specify a tuple. The first value will be the name of the event, followed by
#   the second if the event spans multiple days.
EVENTS = {
        "1-1": "New Year's",
        "14-2": "Valentine's Day",
        "3Mon-2": ("Presidents' Day", "Weekend"),
        "17-3": "St. Patrick's Day",
        "2Sun-5": "Mothers' Day",
        "3Sun-6": "Father's Day",
        "4-7": ("Fourth of July", "Weekend"),
        "1Mon-9": ("Labor Day", "Weekend"),
        "31-10": "Halloween",
        "11-11": ("Veterans Day", "Weekend"),
        "4Thu-11": ("Thanksgiving", "Break"),
        "24-12": "Christmas Eve",
        "25-12": "Christmas",
        "31-12": "New Year's Eve"
    }
event_re = '((?P<wdn>\d{1,2})(?P<wd>Mon|Tue|Wed|Thu|Fri|Sat|Sun)|(?P<d>\d{1,2}))-(?P<m>\d{1,2})'

# Keys should be dates as zero padded day-month-year (simplifies date parsing)
# Value should be the name of the person. Events will be "name's xth birthday".
#
# TODO: Add support for other annual events with a count such as anniversaries.
#       Format will be (name(s), event). Ex ("Bob", "Birthday"), ("Karen and
#       Jim", "Anniversary")
BIRTHDAYS = {
        "16-07-1992": "Cameron and Emily",
        "04-09-1994": "Jake",
        "12-09-1993": "Aisha"
    }

def easterDate(year):
    a = year % 19
    b = year / 100
    c = year % 100
    d = b / 4
    e = b % 4
    f = (b + 8) / 25
    g = (b - f + 1) / 3
    h = (19 * a + b - d - g + 15) % 30
    i = c / 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) / 451
    EasterMonth = (h + l - 7 * m + 114) / 31
    p = (h + l - 7 * m + 114) % 31
    EasterDay = p + 1

    return (EasterMonth, EasterDay)

def getHoliday(date):
    # check if it's a birthday first
    for key, val in BIRTHDAYS.iteritems():
        if datetime.strptime(key, "%d-%m-%Y").month == date.month and datetime.strptime(key, "%d-%m-%Y").day == date.day:
            return (val, datetime.strptime(key, "%d-%m-%Y").year)
    for key, val in EVENTS.iteritems():
        key_match = re.match(event_re, key)
        if key_match:
            if key_match.group('d') and key_match.group('m') and \
                    date.day == int(key_match.group('d')) and date.month == int(key_match.group('m')):
                return val
            elif key_match.group('wdn') and key_match.group('wd') and key_match.group('m') and \
                    date.month == int(key_match.group('m')) and \
                    key_match.group('wd') == datetime.strftime(date, '%a'):
                proper_day = datetime(date.year, date.month, 1)
                adj = (weekdays.index(key_match.group('wd')) - proper_day.weekday()) % 7
                proper_day += timedelta(days = adj)
                proper_day += timedelta(weeks = int(key_match.group('wdn')) - 1)
                if proper_day.day == date.day and proper_day.month == date.month:
                    return val

    if date.month == 3 or date.month == 4:
        easter = easterDate(date.year)
        if easter[0] == date.month and easter[1] == date.day:
            return "Easter"

    return None
