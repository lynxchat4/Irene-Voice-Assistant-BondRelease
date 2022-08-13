from inspect import isgenerator
from typing import Optional, Callable, Generator, Any, TypeVar

from vaabstract import VAContext, VAApi, VAContextSource
from vacommandtree import VACommandTree


def _context_from_function_return(val: Any, va: VAApi) -> Optional[VAContext]:
    if isgenerator(val):
        return GeneratorContext(val).start(va)

    return None


T = TypeVar('T')


class FunctionContext(VAContext):
    """
    Контекст, однократно вызывающий заданную функцию при получении команды.
    """
    __slots__ = ['_fn']

    def __init__(self, fn: Callable[[VAApi, str], Any]):
        self._fn = fn

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return _context_from_function_return(self._fn(va, text), va)

    def __str__(self):
        try:
            return f'{getattr(self._fn, "__module__")}.{self._fn.__qualname__}'
        except AttributeError:
            return str(self._fn)


class FunctionContextWithArgs(VAContext):
    """
    Контекст, однократно вызывающий заданную функцию при получении команды и передающий
    этой функции дополнительный аргумент.
    """
    __slots__ = ['_fn', '_args']

    def __init__(self, fn: Callable[[VAApi, str, T], None], arg: T):
        self._fn = fn
        self._arg = arg

    def handle_command(self, va: VAApi, text: str) -> Optional['VAContext']:
        return _context_from_function_return(self._fn(va, text, self._arg), va)

    def __str__(self):
        try:
            return f'{getattr(self._fn, "__module__")}.{self._fn.__qualname__}'
        except AttributeError:
            return str(self._fn)


class ContextTimeoutException(Exception):
    pass


class GeneratorContext(VAContext):
    __slots__ = ['_gen']

    def __init__(self, generator: Generator[str, str, str]):
        self._gen = generator

    @staticmethod
    def _process_result(va: VAApi, value: Any, default_next_ctx: Optional[VAContext]) -> Optional[VAContext]:
        """
        Обрабатывает значение, yield'нутое или возвращённое генератором.

        Args:
            va:
            value: значение yield'нутое или возвращённое генератором
            default_next_ctx: контекст продолжения диалога для случаев когда значение, полученное от генератора не
            требует смены контекста

        Returns: контекст для продолжения диалога или None для завершения диалога
        """
        if isinstance(value, str):
            va.say(value)

        # TODO: Добавить возможность переключения контекста из генератора.

        return default_next_ctx

    def start(self, va: VAApi) -> Optional[VAContext]:
        try:
            val = next(self._gen)
        except StopIteration:
            return None

        return self._process_result(va, val, self)

    def handle_command(self, va: VAApi, text: str) -> Optional['VAContext']:
        try:
            val = self._gen.send(text)
        except StopIteration as e:
            return self._process_result(va, e.value, None)

        return self._process_result(va, val, self)

    def handle_timeout(self, va: VAApi) -> Optional['VAContext']:
        try:
            val = self._gen.throw(ContextTimeoutException())
        except StopIteration as e:
            return self._process_result(va, e.value, None)
        except ContextTimeoutException:
            # Генератор не перехватил ContextTimeoutException - завершаем диалог
            return None

        return self._process_result(va, val, self)


class CommandTreeContext(VAContext):
    def __init__(self, tree: VACommandTree):
        self._tree = tree

    def handle_command(self, va: VAApi, text: str) -> Optional['VAContext']:
        ctx, arg = self._tree.get_command(text)

        return ctx.handle_command(va, arg)


def construct_context(src: VAContextSource) -> VAContext:
    if isinstance(src, VAContext):
        return src

    if callable(src):
        return FunctionContext(src)

    if isinstance(src, dict):
        tree = VACommandTree[VAContext]()
        tree.add_commands(src, construct_context)
        return CommandTreeContext(tree)

    if isinstance(src, tuple):
        if len(src) >= 1:
            first, *rest = src

            if callable(first):
                fn: Callable = first
                if len(rest) >= 2:
                    return FunctionContextWithArgs(fn, rest[0])
                else:
                    return FunctionContext(fn)

    raise Exception(f'Illegal context source: {src}')
