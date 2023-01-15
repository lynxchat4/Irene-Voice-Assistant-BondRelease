from typing import Collection, TypeVar, Callable

from irene.brain.abc import OutputChannelPool, OutputChannel, OutputChannelNotFoundError

TChan = TypeVar('TChan', bound=OutputChannel)


class OutputPoolImpl(OutputChannelPool, list[OutputChannel]):
    def __init__(self, channels: Collection[OutputChannel]):
        super().__init__(channels)

    def query_channels(self, predicate: Callable[[OutputChannel], bool]) -> Collection[OutputChannel]:
        lst = list(filter(predicate, self))

        if len(lst) == 0:
            raise OutputChannelNotFoundError()

        return lst  # type: ignore


EMPTY_OUTPUT_POOL = OutputPoolImpl(())


class CompositeOutputPool(OutputChannelPool, list[OutputChannelPool]):
    def query_channels(self, predicate: Callable[[OutputChannel], bool]) -> Collection[OutputChannel]:
        result: list[OutputChannel] = []

        for pool in self:
            try:
                result.extend(pool.query_channels(predicate))
            except OutputChannelNotFoundError:
                ...

        if len(result) == 0:
            raise OutputChannelNotFoundError()

        return result
