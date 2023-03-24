from typing import Optional

from irene.brain.abc import InboundMessage, OutputChannelPool
from irene.brain.output_pool import EMPTY_OUTPUT_POOL
from irene.utils.metadata import MetadataMapping


class StubTextMessage(InboundMessage):
    def __init__(self, text: str, meta: Optional[MetadataMapping] = None):
        self._txt = text
        self._meta = meta or {}

    def get_text(self) -> str:
        return self._txt

    def get_related_outputs(self) -> OutputChannelPool:
        return EMPTY_OUTPUT_POOL

    @property
    def meta(self) -> MetadataMapping:
        return self._meta


tm = StubTextMessage
