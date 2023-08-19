from datetime import time
from typing import NamedTuple, Optional, Collection

from irene.constants.time_units_ru import MINUTE
from irene.constants.word_forms import WordCaseRU
from irene.utils.pronounce_numbers_ru import pronounce_integer


class _HourForms(NamedTuple):
    hour: int
    full: str
    partial: str
    unit: Optional[str]
    day_part: str


_HOUR_FORMS: tuple[_HourForms, ...] = (
    _HourForms(0, "двенадцать", "двенадцатого", "часов", "ночи"),
    _HourForms(1, "час", "первого", None, "ночи"),
    _HourForms(2, "два", "второго", "часа", "ночи"),
    _HourForms(3, "три", "третьего", "часа", "ночи"),
    _HourForms(4, "четыре", "четвёртого", "часа", "ночи"),
    _HourForms(5, "пять", "пятого", "часов", "утра"),
    _HourForms(6, "шесть", "шестого", "часов", "утра"),
    _HourForms(7, "семь", "седьмого", "часов", "утра"),
    _HourForms(8, "восемь", "восьмого", "часов", "утра"),
    _HourForms(9, "девять", "девятого", "часов", "утра"),
    _HourForms(10, "десять", "десятого", "часов", "утра"),
    _HourForms(11, "одиннадцать", "одиннадцатого", "часов", "утра"),
    _HourForms(12, "двенадцать", "двенадцатого", "часов", "утра"),
    _HourForms(13, "час", "первого", None, "дня"),
    _HourForms(14, "два", "второго", "часа", "дня"),
    _HourForms(15, "три", "третьего", "часа", "дня"),
    _HourForms(16, "четыре", "четвёртого", "часа", "дня"),
    _HourForms(17, "пять", "пятого", "часов", "вечера"),
    _HourForms(18, "шесть", "шестого", "часов", "вечера"),
    _HourForms(19, "семь", "седьмого", "часов", "вечера"),
    _HourForms(20, "восемь", "восьмого", "часов", "вечера"),
    _HourForms(21, "девять", "девятого", "часов", "вечера"),
    _HourForms(22, "десять", "десятого", "часов", "вечера"),
    _HourForms(23, "одиннадцать", "одиннадцатого", "часов", "вечера"),
)


def pronounce_time_ru(
        t: time,
        *,
        pronounce_hour_units=False,
        half_enabled=True,
        half_short=True,
        half_tolerance_minutes=0,
        quoter_enabled=True,
        quoter_tolerance_minutes=0,
        day_time_enabled=True,
        negative_enabled=True,
        negative_threshold=20,
        negative_units_enabled=False,
        midnight_enabled=True,
        midday_enabled=True,
        pronounce_exactly=True,
        exactly_before=True,
        exactly_tolerance_minutes=0,
) -> Collection[str]:
    result = []

    def append_hour_units_and_day_time(forms: _HourForms, partial: bool):
        """
        "[часов|часа] [утра]"
        """
        if pronounce_hour_units:
            if partial:
                result.append("часа")
            elif forms.unit is not None:
                result.append(forms.unit)

        if day_time_enabled:
            result.append(forms.day_part)

    def append_full(forms: _HourForms):
        """
        "девять [часов] [утра]"
        """
        if midnight_enabled and forms.hour == 0:
            result.append("полночь")
        elif midday_enabled and forms.hour == 12:
            result.append("полдень")
        else:
            result.append(forms.full)

            append_hour_units_and_day_time(forms, False)

    def append_exactly(forms: _HourForms):
        """
        "[ровно] девять [часов] [утра] [ровно]"
        """
        if pronounce_exactly and exactly_before:
            result.append("ровно")

        append_full(forms)

        if pronounce_exactly and not exactly_before:
            result.append("ровно")

    if t.minute <= exactly_tolerance_minutes:
        # "[ровно] девять [часов] [утра] [ровно]" @ 09:00; 09:01, exactly_tolerance_minutes >= 1
        append_exactly(_HOUR_FORMS[t.hour])
    else:
        next_hour_forms: _HourForms = _HOUR_FORMS[(t.hour + 1) % len(_HOUR_FORMS)]

        if t.minute >= (60 - exactly_tolerance_minutes):
            # "[ровно] девять [часов] [утра] [ровно]" @ 08:59, exactly_tolerance_minutes >= 1
            append_exactly(next_hour_forms)
        elif half_enabled and abs(t.minute - 30) <= half_tolerance_minutes:
            # "пол[овина] девятого [часа] [утра]" @ 08:30
            result.append("пол" if half_short else "половина")
            result.append(next_hour_forms.partial)
            append_hour_units_and_day_time(next_hour_forms, False)
        elif quoter_enabled and abs(t.minute - 15) <= quoter_tolerance_minutes:
            # "четверть девятого [часа] [утра]" @ 08:15
            result.append("четверть")
            result.append(next_hour_forms.partial)
            append_hour_units_and_day_time(next_hour_forms, False)
        elif negative_enabled and t.minute >= (60 - negative_threshold):
            # "без (четверти|пятнадцати [минут]) девять [часов] [утра]" @ 08:45
            result.append("без")

            if quoter_enabled and abs(t.minute - 45) <= quoter_tolerance_minutes:
                result.append("четверти")
            else:
                minutes_left = 60 - t.minute
                if minutes_left == 1:
                    result.append("минуты")
                else:
                    result.extend(pronounce_integer(minutes_left, MINUTE, WordCaseRU.GENITIVE))

                    if not negative_units_enabled:
                        result.pop()

            append_full(next_hour_forms)
        else:
            # "двадцать минут девятого [часа] [утра]"
            result.extend(pronounce_integer(t.minute, MINUTE, WordCaseRU.NOMINATIVE))
            result.append(next_hour_forms.partial)
            append_hour_units_and_day_time(next_hour_forms, True)

    return result
