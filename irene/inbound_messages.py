from irene.canonical_text import convert_to_canonical
from irene.va_abc import InboundMessage, OutputChannelPool


class PlainTextMessage(InboundMessage):
    __slots__ = ('_canonical', '_txt', '_out')

    def __init__(self, text: str, outputs: OutputChannelPool):
        self._canonical = convert_to_canonical(text)
        self._txt = text
        self._out = outputs

    def get_text(self) -> str:
        return self._canonical

    def get_original_text(self) -> str:
        return self._txt

    def get_related_outputs(self) -> OutputChannelPool:
        return self._out


class PartialTextMessage(InboundMessage):
    __slots__ = ('_original', '_text')

    def __init__(self, original: InboundMessage, text_slice: str):
        self._original = original
        self._text = convert_to_canonical(text_slice)

    def get_text(self) -> str:
        return self._text

    def get_related_outputs(self) -> OutputChannelPool:
        return self._original.get_related_outputs()

    def get_original(self) -> 'InboundMessage':
        return self._original
