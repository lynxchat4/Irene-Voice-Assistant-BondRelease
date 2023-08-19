from enum import Enum
from typing import NamedTuple

from irene.constants.gender import GenderCode


class WordCaseRU(Enum):
    """Перечисление падежей русского языка"""

    NOMINATIVE = 'nominative'
    GENITIVE = 'genitive'
    DATIVE = 'dative'
    ACCUSATIVE = 'accusative'
    INSTRUMENTAL = 'instrumental'
    PREPOSITIONAL = 'prepositional'

    def format_check_phrase(self, phrase) -> str:
        if self is WordCaseRU.NOMINATIVE:
            return f"У меня есть {phrase}"
        if self is WordCaseRU.GENITIVE:
            return f"У меня нет {phrase}"
        if self is WordCaseRU.DATIVE:
            return f"Я рад {phrase}"
        if self is WordCaseRU.ACCUSATIVE:
            return f"Я вижу {phrase}"
        if self is WordCaseRU.INSTRUMENTAL:
            return f"Я доволен {phrase}"
        if self is WordCaseRU.PREPOSITIONAL:
            return f"Я думаю о {phrase}"

        assert False, self


class KnownFormsRU(NamedTuple):
    """Описывает формы существительного на русском языке."""

    nominative: str
    """Именительный падеж. Кто/Что?"""

    genitive: str
    """Родительный падеж. Кого/Чего?"""

    dative: str
    """Дательный падеж. Кому/Чему?"""

    accusative: str
    """Винительный падеж. Кого/Что?"""

    instrumental: str
    """Творительный падеж. Кем/Чем?"""

    prepositional: str
    """Предложный падеж. О ком/чём?"""

    def get_for_case(self, case: WordCaseRU) -> str:
        return getattr(self, case.value)


class FullKnownFormsRU(NamedTuple):
    singular: KnownFormsRU
    """Формы единственного числа"""

    plural: KnownFormsRU
    """Формы множественного числа"""

    gender: GenderCode
    """Род"""

    animated: bool = False
    """Одушевлённое/неодушевлённое"""
