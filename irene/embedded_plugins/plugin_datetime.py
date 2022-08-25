from datetime import datetime

from irene import VAApiExt
from irene.utils.num_to_text_ru import num2text

name = 'datetime'
version = '2.0'

config = {
    "sayNoon": False,
    "skipUnits": False,
    "unitsSeparator": ", ",
    "skipMinutesWhenZero": True,
}

config_comment = """
Настройки вывода даты и времени.
Доступны следующие параметры:

sayNoon             - говорить "полдень" и "полночь" вместо 12 и 0 часов
skipUnits           - не произносить единицы времени ("час", "минуты")
unitsSeparator      - сепаратор при озвучивании 10 часов<unitsSeparator>10 минут. Варианты: " и "
skipMinutesWhenZero - не озвучивать минуты, если равны 0
"""


def _play_date(va: VAApiExt, _phrase: str):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    weekday = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"][datetime.weekday(now)]
    va.say("сегодня " + weekday + ", " + _get_date(date))


def _get_date(date):
    day_list = ['первое', 'второе', 'третье', 'четвёртое',
                'пятое', 'шестое', 'седьмое', 'восьмое',
                'девятое', 'десятое', 'одиннадцатое', 'двенадцатое',
                'тринадцатое', 'четырнадцатое', 'пятнадцатое', 'шестнадцатое',
                'семнадцатое', 'восемнадцатое', 'девятнадцатое', 'двадцатое',
                'двадцать первое', 'двадцать второе', 'двадцать третье',
                'двадцать четвёртое', 'двадцать пятое', 'двадцать шестое',
                'двадцать седьмое', 'двадцать восьмое', 'двадцать девятое',
                'тридцатое', 'тридцать первое']
    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    date_list = date.split('-')
    return (day_list[int(date_list[2]) - 1] + ' ' +
            month_list[int(date_list[1]) - 1] + ' '
            )


def _play_time(va: VAApiExt, _phrase: str):
    if config["skipUnits"]:
        units_minutes = (('', '', ''), 'f')
        units_hours = (('', '', ''), 'm')
    else:
        units_minutes = ((u'минута', u'минуты', u'минут'), 'f')
        units_hours = ((u'час', u'часа', u'часов'), 'm')

    now = datetime.now()
    hours = int(now.strftime("%H"))
    minutes = int(now.strftime("%M"))

    if config["sayNoon"]:
        if hours == 0 and minutes == 0:
            va.say("Сейчас ровно полночь")
            return
        elif hours == 12 and minutes == 0:
            va.say("Сейчас ровно полдень")
            return

    txt = num2text(hours, units_hours)
    if minutes > 0 or config["skipMinutesWhenZero"] is not True:
        txt = "Сейчас " + txt
        if not config["skipUnits"]:
            txt += config["unitsSeparator"]
        txt += num2text(minutes, units_minutes)
    else:
        txt = "Сейчас ровно " + txt

    va.say(txt)


define_commands = {
    "дата": _play_date,
    "время": _play_time,
}
