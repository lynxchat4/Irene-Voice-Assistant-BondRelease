from inspect import isclass
from typing import Optional, Callable

from irene.brain.abc import VAActiveInteraction, VAApi, VAContext, VAContextGenerator, VAActiveInteractionSource, \
    VAApiExt, InboundMessage, VAContextConstructor
from irene.brain.contexts import ApiExtProvider


class FunctionActiveInteraction(VAActiveInteraction):
    """
    Активное взаимодействие заданное функцией.
    """
    __slots__ = ('_src', '_msg', '_construct_context')

    def __init__(
            self,
            src: Callable[[VAApiExt], Optional[VAContextGenerator]],
            msg: Optional[InboundMessage],
            context_constructor: VAContextConstructor,
    ):
        self._src = src
        self._msg = msg
        self._construct_context = context_constructor

    def act(self, va: VAApi) -> Optional[VAContext]:
        ext = ApiExtProvider(self._construct_context)

        if self._msg is not None:
            ext.set_inbound_message(self._msg)

        return ext.get_next_context_from_returned_value(self._src(ext.using_va(va)), va)


def construct_active_interaction(
        src: VAActiveInteractionSource,
        *,
        construct_context: VAContextConstructor,
        related_message: Optional[InboundMessage] = None,
) -> VAActiveInteraction:
    if isinstance(src, VAActiveInteraction):
        return src

    if isclass(src) and issubclass(src, VAActiveInteraction):
        return src()

    if callable(src):
        return FunctionActiveInteraction(src, related_message, construct_context)

    raise TypeError(f'Попытка создать активное взаимодействие из объекта неподдерживаемого типа ({type(src)}): {src}')
