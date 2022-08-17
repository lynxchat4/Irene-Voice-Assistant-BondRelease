from typing import Optional, Callable

from vaabstract import VAActiveInteraction, VAApi, VAContext, VAContextGenerator, VAActiveInteractionSource, VAApiExt
from vacontext import ApiExtProvider


class FunctionActiveInteraction(VAActiveInteraction):
    """
    Активное взаимодействие заданное функцией.
    """
    __slots__ = ['_src']

    def __init__(self, src: Callable[[VAApiExt], Optional[VAContextGenerator]]):
        self._src = src

    def act(self, va: VAApi) -> Optional[VAContext]:
        ext = ApiExtProvider()

        return ext.get_next_context_from_returned_value(self._src(ext.using_va(va)), va)


def construct_active_interaction(src: VAActiveInteractionSource) -> VAActiveInteraction:
    if isinstance(src, VAActiveInteraction):
        return src

    if callable(src):
        return FunctionActiveInteraction(src)

    raise Exception(f'Illegal active interaction source: {src}')
