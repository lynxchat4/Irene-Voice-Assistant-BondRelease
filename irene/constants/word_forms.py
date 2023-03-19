from typing import NamedTuple


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
