from typing import Optional

from irene.brain.abc import InboundMessage, OutputChannelPool
from irene.brain.canonical_text import convert_to_canonical
from irene.utils.metadata import MetadataMapping


class PlainTextMessage(InboundMessage):
    """
    Простое текстовое сообщение, не подвергнутое никаким преобразованиям.
    """
    __slots__ = ('_canonical', '_txt', '_out', '_meta')

    def __init__(
            self,
            text: str,
            outputs: OutputChannelPool,
            meta: Optional[MetadataMapping] = None,
    ):
        self._canonical = convert_to_canonical(text)
        self._txt = text
        self._out = outputs
        self._meta = meta if meta is not None else {}

    def get_text(self) -> str:
        return self._canonical

    def get_original_text(self) -> str:
        return self._txt

    def get_related_outputs(self) -> OutputChannelPool:
        return self._out

    @property
    def meta(self) -> MetadataMapping:
        return self._meta


class PartialTextMessage(InboundMessage):
    """
    Остаток сообщения, часть которого уже была использована для выбора обработчика.
    """

    __slots__ = ('_original', '_text', '_meta')

    def __init__(
            self,
            original: InboundMessage,
            text_slice: str,
            meta_overrides: Optional[MetadataMapping] = None
    ):
        self._original = original.get_original()
        self._text = convert_to_canonical(text_slice)
        self._meta = original.meta if meta_overrides is None else {**original.meta, **meta_overrides}

    def get_text(self) -> str:
        return self._text

    def get_related_outputs(self) -> OutputChannelPool:
        return self._original.get_related_outputs()

    def get_original(self) -> InboundMessage:
        return self._original

    @property
    def meta(self) -> MetadataMapping:
        return self._meta
