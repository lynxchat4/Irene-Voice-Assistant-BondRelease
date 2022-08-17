from typing import Type, Collection, TypeVar

from irene.va_abc import OutputChannelPool, OutputChannel, OutputChannelNotFoundError

TChan = TypeVar('TChan', bound=OutputChannel)


class OutputPoolImpl(OutputChannelPool):
    __slots__ = '_channels'

    def __init__(self, channels: Collection[OutputChannel]):
        self._channels = channels

    def get_channels(self, typ: Type[TChan]) -> Collection[TChan]:
        lst = list(filter(typ.__instancecheck__, self._channels))

        if len(lst) == 0:
            raise OutputChannelNotFoundError(typ)

        return lst  # type: ignore


EMPTY_OUTPUT_POOL = OutputPoolImpl(())
