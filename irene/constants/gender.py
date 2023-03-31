from typing import NamedTuple, Literal

# TODO: Добавить шутку о том, что есть только два гендера.

GenderCode = Literal[
    'female', 'male', 'neuter', 'plural',
]


class GenderDefinition(NamedTuple):
    """
    Описывает гендер (род).
    """
    code: GenderCode

    @property
    def label(self) -> str:
        return f"gender.{self.code}"


FEMALE = GenderDefinition(
    # Женский род, "Я, Ирина"
    code='female',
)

MALE = GenderDefinition(
    # Мужской род, "Я, Джарвис"
    code='male',
)

NEUTER = GenderDefinition(
    # Средний род, "Я, программное обеспечение"
    code='neuter',
)

PLURAL = GenderDefinition(
    # Множественное число, "Мы, множество гномиков, живущих в твоём компьютере"
    code='plural',
)

ALL_GENDERS = (FEMALE, MALE, NEUTER, PLURAL)

ALL_GENDER_META_LABELS = (gender.label for gender in ALL_GENDERS)
