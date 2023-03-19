from typing import Any

from irene.constants.gender import ALL_GENDER_META_LABELS
from irene.constants.languages import ALL_LANGUAGE_META_LABELS


def language_independent_channel_labels() -> dict[str, Any]:
    return {label: True for label in ALL_LANGUAGE_META_LABELS}


def gender_independent_channel_labels() -> dict[str, Any]:
    return {label: True for label in ALL_GENDER_META_LABELS}


def pure_text_channel_labels() -> dict[str, Any]:
    """
    Создаёт набор меток для канала вывода (как правило, текстового), позволяющего выводить текст от имени ассистента
    любого пола, на любом языке.
    """
    return {
        **language_independent_channel_labels(),
        **gender_independent_channel_labels(),
    }
