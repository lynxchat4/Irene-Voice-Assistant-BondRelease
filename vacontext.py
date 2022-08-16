from inspect import isgenerator
from logging import getLogger
from typing import Optional, Callable, Any, TypeVar, Collection, Iterable

from vaabstract import VAContext, VAApi, VAContextSource, VAContextGenerator
from vacommandtree import VACommandTree, NoCommandMatchesException, AmbiguousCommandException


def context_from_function_return(val: Any, va: VAApi) -> Optional[VAContext]:
    """
    Создаёт контекст из возвращаемого значения функции, использованной для создания контекста или активного
    взаимодействия.

    Args:
        val: значение, возвращённое функцией
        va:

    Returns:
        созданный контекст
    """
    if isgenerator(val):
        # Генератор не запускается сразу после вызова функции.
        # Метод start в GeneratorContext прогонит генератор до первого yield`а (или return`а, или raise)
        return GeneratorContext(val).start(va)

    return None


T = TypeVar('T')


class FunctionContext(VAContext):
    """
    Контекст, однократно вызывающий заданную функцию при получении команды.
    """
    __slots__ = '_fn'

    def __init__(self, fn: Callable[[VAApi, str], Any]):
        self._fn = fn

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return context_from_function_return(self._fn(va, text), va)

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
    __slots__ = ('_fn', '_args')

    def __init__(self, fn: Callable[[VAApi, str, T], None], arg: T):
        self._fn = fn
        self._arg = arg

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return context_from_function_return(self._fn(va, text, self._arg), va)

    def __str__(self):
        try:
            return f'{getattr(self._fn, "__module__")}.{self._fn.__qualname__}'
        except AttributeError:
            return str(self._fn)


class ContextTimeoutException(Exception):
    pass


class GeneratorContext(VAContext):
    """
    Контекст, поведение которого определяется генератором.
    FunctionContext и FunctionContextWithArgs создают такой контекст когда функция возвращает генератор.

    Новые полученные команды отправляются генератору через метод send(), значения, сгенерированные генератором
    воспринимаются как реплики ассистента.

    def play_game(va: VAApi, phrase: str) -> VAContextGenerator:
        # yield со значением - произносит фразу и ожидает ответа
        phrase = yield "Скажи правила или начать"

        while True:
            match phrase:
                case "отмена":
                    # return со значением завершает диалог
                    return "Поняла, играть не будем"
                case "правила":
                    phrase = yield "Правила игры. Я загадываю число ... блаблабла"
                case "начать" | "повторить":
                    try:
                        ...
                    except ContextTimeoutException:
                        # yield кидает ContextTimeoutException когда пользователь не отвечает слишком долго
                        phrase = yield "Ты слишком долго думал." \
                            "Засчитываю техническое поражение. Скажи повторить чтобы начать снова."
                case _:
                    phrase = yield "Не поняла..."
    """
    __slots__ = '_gen'

    def __init__(self, generator: VAContextGenerator):
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
    """
    Контекст, интерпретирующий команды с помощью дерева команд (VACommandTree).
    """
    __slots__ = ('_tree', '_unknown_command_context', '_ambiguous_command_context')

    logger = getLogger('CommandTreeContext')

    def __init__(
            self,
            tree: VACommandTree,
            unknown_command_context: VAContext,
            ambiguous_command_context: Optional[VAContext] = None,
    ):
        """
        Args:
            tree: дерево команд
            unknown_command_context: контекст, которому будут переданы нераспознанные команды
            ambiguous_command_context: контекст, которому будут переданы неоднозначно распознанные команды.
                По-умолчанию, будет использоваться unknown_command_context.
        """
        self._tree = tree
        self._unknown_command_context = unknown_command_context
        self._ambiguous_command_context = ambiguous_command_context or unknown_command_context

    def handle_command(self, va: VAApi, text: str) -> Optional['VAContext']:
        try:
            ctx, arg = self._tree.get_command(text)
        except NoCommandMatchesException as e:
            self.logger.info(str(e))

            return self._unknown_command_context.handle_command(va, text)
        except AmbiguousCommandException as e:
            self.logger.info(str(e))

            return self._ambiguous_command_context.handle_command(va, text)

        return ctx.handle_command(va, arg)


class TriggerPhraseContext(VAContext):
    """
    Контекст, ожидающий появления во входящем потоке ключевой фразы (имени ассистента) и передающий управление
    следующему контексту при его обнаружении.
    """
    __slots__ = ('_phrases', '_next_context')

    def __init__(self, phrases: Collection[Collection[str]], next_context: VAContext):
        """
        Args:
            phrases: набор ключевых фраз. Каждая фраза представлена как коллекция слов.
            next_context: контекст, которому нужно передать управление в случае обнаружения ключевой фразы.
                Остаток фразы будет передан в метод handle_command этого контекста.
        """
        self._phrases = phrases
        self._next_context = next_context

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        words = text.split(' ')

        while len(words) > 0:
            for phrase in self._phrases:
                if words[:len(phrase)] == phrase:
                    rest_text = ' '.join(words[len(phrase):])

                    return self._next_context.handle_command(va, rest_text)

            words = words[1:]

        return None


class InterruptContext(VAContext):
    """
    Контекст, который создаётся когда текущий диалог прерывается новым диалогом "по инициативе" ассистента.

    Делегирует все операции контексту прерывающего диалога.
    Когда тот завершается - возвращается к прерванному диалогу.
    """
    __slots__ = ('_interrupted', '_current')

    def __init__(self, interrupted: VAContext, current: VAContext):
        """
        Args:
            interrupted: контекст прерванного диалога.
                         Метод handle_interrupt прерванного контекста должен быть вызван до создания InterruptContext.
            current: контекст прерывающего диалога.
        """
        self._interrupted = interrupted
        self._current = current

    def _process_next_ctx(self, va: VAApi, ctx: Optional[VAContext]) -> Optional[VAContext]:
        if ctx is None:
            return self._interrupted.handle_restore(va)

        self._current = ctx
        return self

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return self._process_next_ctx(va, self._current.handle_command(va, text))

    def handle_timeout(self, va: VAApi) -> Optional[VAContext]:
        return self._process_next_ctx(va, self._current.handle_timeout(va))

    def get_timeout(self, default: float) -> float:
        return self._current.get_timeout(default)

    def handle_interrupt(self, va: VAApi) -> Optional[VAContext]:
        return self._process_next_ctx(va, self._current.handle_interrupt(va))

    def handle_restore(self, va: VAApi) -> Optional[VAContext]:
        return self._process_next_ctx(va, self._current.handle_restore(va))


class NoopContext(VAContext):
    """
    Контекст, который ничего не делает.

    Null-object от класса контекстов.
    """
    __slots__: Iterable[str] = ()

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return None


class BaseContextWrapper(VAContext):
    """
    Базовый класс для обёрток над контекстом.
    """
    __slots__ = '_wrapped'

    def __init__(self, wrapped: VAContext):
        self._wrapped = wrapped

    def _wrap_next(self, ctx: Optional[VAContext]) -> Optional[VAContext]:
        if ctx is self._wrapped:
            return self._wrapped

        return ctx

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return self._wrap_next(self._wrapped.handle_command(va, text))

    def handle_timeout(self, va: VAApi) -> Optional[VAContext]:
        return self._wrap_next(self._wrapped.handle_timeout(va))

    def handle_interrupt(self, va: VAApi) -> Optional[VAContext]:
        return self._wrap_next(self._wrapped.handle_interrupt(va))

    def handle_restore(self, va: VAApi) -> Optional[VAContext]:
        return self._wrap_next(self._wrapped.handle_restore(va))

    def get_timeout(self, default: float) -> float:
        return self._wrapped.get_timeout(default)


class TimeoutOverrideContext(BaseContextWrapper):
    """
    Обёртка для контекста, добавляющая нестандартный таймаут (интервал ожидания следующей команды).
    """
    __slots__ = '_timeout'

    def __init__(self, wrapped: VAContext, timeout: float):
        super().__init__(wrapped)
        self._timeout = timeout

    def get_timeout(self, default: float) -> float:
        return self._timeout


def construct_context(
        src: VAContextSource,
        *,
        unknown_command_context: VAContext = NoopContext(),
        ambiguous_command_context: Optional[VAContext] = None,
) -> VAContext:
    """
    Создаёт контекст диалога из исходного объекта:

    - из функции - контекст, вызывающий эту функцию (см. ``FunctionContext``)

    - из кортежа с функцией и параметром - контекст, вызывающий эту функцию с этим параметром
      (см. ``FunctionContextWithArgs``)

    - из словаря со строковыми ключами - строит дерево команд (см. ``VACommandTree``) и создаёт на его основе контекст
      (см. ``CommandTreeContext``)

    - если переданный объект уже является контекстом - то он возвращается без изменений

    Args:
        src:
            исходный объект - функция, кортеж из функции и аргумента, словарь или уже готовый контекст
        unknown_command_context:
            контекст, обрабатывающий нераспознанные команды в случае создания CommandTreeContext из словаря.
        ambiguous_command_context:
            контекст, обрабатывающий неоднозначно распознанные команды в случае создания CommandTreeContext из словаря.

    Returns:
        готовый контекст
    """
    if isinstance(src, VAContext):
        return src

    if callable(src):
        return FunctionContext(src)

    if isinstance(src, dict):
        tree = VACommandTree[VAContext]()
        tree.add_commands(src, construct_context)
        return CommandTreeContext(tree, unknown_command_context, ambiguous_command_context)

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
