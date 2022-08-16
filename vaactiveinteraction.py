from typing import Optional, Callable

from vaabstract import VAActiveInteraction, VAApi, VAContext, VAContextGenerator, VAActiveInteractionSource
from vacontext import context_from_function_return


class FunctionActiveInteraction(VAActiveInteraction):
    """
    Активное взаимодействие заданное функцией.
    """
    __slots__ = ['_src']

    def __init__(self, src: Callable[[VAApi], Optional[VAContextGenerator]]):
        self._src = src

    def act(self, va: VAApi) -> Optional[VAContext]:
        return context_from_function_return(self._src(va), va)


def construct_active_interaction(src: VAActiveInteractionSource) -> VAActiveInteraction:
    if isinstance(src, VAActiveInteraction):
        return src

    if callable(src):
        return FunctionActiveInteraction(src)

    raise Exception(f'Illegal active interaction source: {src}')
