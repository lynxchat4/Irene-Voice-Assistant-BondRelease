from irene.output_pool import EMPTY_OUTPUT_POOL
from irene.va_abc import InboundMessage, OutputChannelPool


class StubTextMessage(InboundMessage):
    def __init__(self, text: str):
        self._txt = text

    def get_text(self) -> str:
        return self._txt

    def get_related_outputs(self) -> OutputChannelPool:
        return EMPTY_OUTPUT_POOL


tm = StubTextMessage
