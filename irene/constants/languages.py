from typing import NamedTuple, Iterable, Literal

from irene.constants.word_forms import KnownFormsRU

LanguageCodeShort = Literal[
    'ru', 'en', 'de',
]

LanguageCodeFull = Literal[
    'ru-RU', 'en-US', 'de-DE',
]


class LanguageDefinition(NamedTuple):
    """
    Содержит константы, связанные с некоторым естественным языком - его условные обозначения, его название и производные
    от него слова.
    """

    code: LanguageCodeShort
    """Короткий код языка. Например, "ru"."""

    code_full: LanguageCodeFull
    """Полный код языка. Например, "ru-RU"."""

    known_ru: KnownFormsRU
    """Название языка в русском языке, со всеми падежами."""

    adverb_ru: str
    """Наречие, означающее использование этого языка. Например, "по-русски"."""

    @property
    def labels(self) -> Iterable[str]:
        """
        Ключи метаданных, которые могут использоваться для отметки каналов вывода, поддерживающих этот язык.
        """

        yield f"language.{self.code_full}"

        if self.code_full != self.code:
            yield f"language.{self.code}"


RUSSIAN = LanguageDefinition(
    code='ru',
    code_full='ru-RU',
    known_ru=KnownFormsRU(
        nominative="русский",
        genitive="русского",
        dative="русскому",
        accusative="русского",
        instrumental="русским",
        prepositional="русском",
    ),
    adverb_ru="по-русски",
)

ENGLISH = LanguageDefinition(
    code='en',
    code_full='en-US',
    known_ru=KnownFormsRU(
        nominative="английский",
        genitive="английского",
        dative="английскому",
        accusative="английского",
        instrumental="английским",
        prepositional="английском",
    ),
    adverb_ru="по-английски",
)

GERMAN = LanguageDefinition(
    code='de',
    code_full='de-DE',
    known_ru=KnownFormsRU(
        nominative="немецкий",
        genitive="немецкого",
        dative="немецкому",
        accusative="немецкого",
        instrumental="немецким",
        prepositional="немецком",
    ),
    adverb_ru="по-немецки",
)

ALL_LANGUAGES = (
    RUSSIAN, ENGLISH, GERMAN,
)

ALL_LANGUAGE_META_LABELS = tuple(
    label for language in ALL_LANGUAGES for label in language.labels
)
