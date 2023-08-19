from datetime import datetime
from typing import TypedDict, Optional

from irene import VAApiExt
from irene.utils.probabilistic_flag import ProbabilisticFlag, get_probabilistic_flag
from irene.utils.pronounce_time_ru import pronounce_time_ru

name = 'skill_time'
version = '3.0.0'


class _Config(TypedDict):
    pronounce_hour_units: ProbabilisticFlag
    half_enabled: ProbabilisticFlag
    half_short: ProbabilisticFlag
    half_tolerance_minutes: int
    quarter_enabled: ProbabilisticFlag
    quarter_tolerance_minutes: int
    day_time_enabled: ProbabilisticFlag
    negative_enabled: ProbabilisticFlag
    negative_threshold: int
    negative_units_enabled: ProbabilisticFlag
    midnight_enabled: ProbabilisticFlag
    midday_enabled: ProbabilisticFlag
    pronounce_exactly: ProbabilisticFlag
    exactly_before: ProbabilisticFlag
    exactly_tolerance_minutes: int
    prefix: Optional[str]
    digital_format: ProbabilisticFlag
    digital_format_separator: Optional[str]
    digital_pronounce_minute_units: ProbabilisticFlag
    digital_skip_minutes_when_zero: ProbabilisticFlag


config: _Config = {
    'pronounce_hour_units': 0.2,
    'half_enabled': 0.9,
    'half_short': 0.5,
    'half_tolerance_minutes': 0,
    'quarter_enabled': 0.8,
    'quarter_tolerance_minutes': 0,
    'day_time_enabled': True,
    'negative_enabled': 0.9,
    'negative_threshold': 20,
    'negative_units_enabled': 0.1,
    'midnight_enabled': 0.9,
    'midday_enabled': 0.9,
    'pronounce_exactly': 0.9,
    'exactly_before': 0.5,
    'exactly_tolerance_minutes': 0,
    'prefix': "Сейчас",
    'digital_format': False,
    'digital_format_separator': "и",
    'digital_pronounce_minute_units': False,
    'digital_skip_minutes_when_zero': 0.5,
}

config_comment = """
Настройки вывода даты.

Доступны следующие параметры:
- ``pronounce_hour_units``            - нужно ли произносить слова "час"/"часа"/"часов"
- ``half_enabled``                    - произносить "половина" вместо "30 минут"
- ``half_short``                      - произносить "пол" вместо "половина"
- ``half_tolerance_minutes``          - в +- скольких минутах от точной середины часа говорить, что сейчас половина часа.
                                        Например, если здесь будет 2, то половиной будет считаться время с 28 до 32 минут.
- ``quarter_enabled``                 - произносить "четверть"/"без четверти" вместо "15 минут"/"без 15 минут"
- ``quarter_tolerance_minutes``       - в +- скольких минутах от 15/45 минут произносить "четверть"/"без четверти".
                                        Аналогично ``half_tolerance_minutes``.
- ``day_time_enabled``                - указывать часы утра/дня/вечера/ночи.
- ``negative_enabled``                - использовать форму "без N (минут) M (часов)"
- ``negative_threshold``              - со скольки минут до ровного часа можно использовать форму "без N (минут) M (часов)"
- ``negative_units_enabled``          - произносить "минут" в "без N (минут) M (часов)"
- ``midnight_enabled``                - использовать "полночь" вместо "12го часа ночи", где уместно
- ``midday_enabled``                  - использовать "полдень" вместо "12 часа утра", где уместно
- ``pronounce_exactly``               - произносить слово "ровно"
- ``exactly_before``                  - произносить "ровно" до, а не после времени. Т.е "ровно 12 часов"
- ``exactly_tolerance_minutes``       - в +- скольких минутах от ровного часа произносить время как будто час ровный.
                                        Аналогично ``half_tolerance_minutes``.
- ``digital_format``                  - использовать 24х часовой формат вместо 12ти часового
- ``digital_format_separator``        - разделитель между часами и минутами в 24х часовом формате
- ``digital_pronounce_minute_units``  - произносить "минута"/"минут" в 24х часовом формате
- ``digital_skip_minutes_when_zero``  - пропускать минуты в 24х часовом формате если их 0

Для параметров ``pronounce_hour_units``, ``half_enabled``, ``half_short``, ``day_time_enabled`` и прочих можно
использовать как флаг (``true``/``false``), так и значение вероятности (от 0.0 до 1.0), с которым для этого параметра
будет выбрано значение.
Если вместо флага указана вероятность, то значение флага выбирается случайно при каждом выполнении команды.
"""


def _play_time(va: VAApiExt, _phrase: str):
    pronounced_time = list(pronounce_time_ru(
        datetime.now().time(),
        half_tolerance_minutes=config['half_tolerance_minutes'],
        quarter_tolerance_minutes=config['quarter_tolerance_minutes'],
        negative_threshold=config['negative_threshold'],
        exactly_tolerance_minutes=config['exactly_tolerance_minutes'],
        digital_format_separator=config['digital_format_separator'],
        pronounce_hour_units=get_probabilistic_flag(config['pronounce_hour_units']),
        half_enabled=get_probabilistic_flag(config['half_enabled']),
        half_short=get_probabilistic_flag(config['half_short']),
        quarter_enabled=get_probabilistic_flag(config['quarter_enabled']),
        day_time_enabled=get_probabilistic_flag(config['day_time_enabled']),
        negative_enabled=get_probabilistic_flag(config['negative_enabled']),
        negative_units_enabled=get_probabilistic_flag(config['negative_units_enabled']),
        midnight_enabled=get_probabilistic_flag(config['midnight_enabled']),
        midday_enabled=get_probabilistic_flag(config['midday_enabled']),
        pronounce_exactly=get_probabilistic_flag(config['pronounce_exactly']),
        exactly_before=get_probabilistic_flag(config['exactly_before']),
        digital_format=get_probabilistic_flag(config['digital_format']),
        digital_pronounce_minute_units=get_probabilistic_flag(config['digital_pronounce_minute_units']),
        digital_skip_minutes_when_zero=get_probabilistic_flag(config['digital_skip_minutes_when_zero']),
    ))

    if (prefix := config['prefix']) is not None:
        pronounced_time.insert(0, prefix)

    va.say(' '.join(pronounced_time))


define_commands = {
    "время|сколько времени": _play_time,
}
