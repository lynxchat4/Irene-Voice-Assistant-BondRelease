from typing import Type, Collection, TypeVar

from irene.brain.abc import OutputChannelPool, OutputChannel, OutputChannelNotFoundError

TChan = TypeVar('TChan', bound=OutputChannel)


class OutputPoolImpl(OutputChannelPool, list[OutputChannel]):
    def __init__(self, channels: Collection[OutputChannel]):
        super().__init__(channels)

    def get_channels(self, typ: Type[TChan]) -> Collection[TChan]:
        lst = list(filter(typ.__instancecheck__, self))

        if len(lst) == 0:
            raise OutputChannelNotFoundError(typ)

        return lst  # type: ignore


EMPTY_OUTPUT_POOL = OutputPoolImpl(())


class CompositeOutputPool(OutputChannelPool, list[OutputChannelPool]):
    def get_channels(self, typ: Type[TChan]) -> Collection[TChan]:
        result: list[TChan] = []

        for pool in self:
            try:
                result.extend(pool.get_channels(typ))
            except OutputChannelNotFoundError:
                ...

        if len(result) == 0:
            raise OutputChannelNotFoundError(typ)

        return result
