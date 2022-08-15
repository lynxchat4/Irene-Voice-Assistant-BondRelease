from inspect import isgenerator
from typing import Optional, Callable, Any, TypeVar, Collection

from vaabstract import VAContext, VAApi, VAContextSource, VAContextGenerator
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

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return _context_from_function_return(self._fn(va, text, self._arg), va)

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
    __slots__ = ['_gen']

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
    __slots__ = ['_tree']

    def __init__(self, tree: VACommandTree):
        self._tree = tree

    def handle_command(self, va: VAApi, text: str) -> Optional['VAContext']:
        ctx, arg = self._tree.get_command(text)

        return ctx.handle_command(va, arg)


class TriggerPhraseContext(VAContext):
    """
    Контекст, ожидающий появления во входящем потоке ключевой фразы (имени ассистента) и передающий управление
    следующему контексту при его обнаружении.
    """
    __slots__ = ['_phrases', '_next_context']

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
