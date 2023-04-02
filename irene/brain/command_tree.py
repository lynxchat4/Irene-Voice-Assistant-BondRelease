from typing import Collection, Generator, Optional, Generic, TypeVar, Union, Callable, Tuple, Any

__all__ = [
    'VACommandTree',
    'ConflictingCommandsException',
    'NoCommandMatchesException',
    'AmbiguousCommandException',
]

T = TypeVar('T')

TSrc = TypeVar('TSrc')

# TSrcDict = dict[str, Union['TSrcDict', TSrc]] # пока не поддерживается в mypy
TSrcDict = dict[str, Union[Any, TSrc]]

TConstructor = Callable[[TSrc], T]


class _CommandMatch(Generic[T]):
    __slots__ = ('ctx', 'text', 'weight')

    def __init__(self, ctx: T, text_arg: str, weight: float):
        self.ctx = ctx
        self.text = text_arg
        self.weight = weight

    def __str__(self):
        return f'{self.ctx}({self.text}) * {self.weight}'

    def weight_is_close_to(self, other: '_CommandMatch'):
        return abs(self.weight - other.weight) < 0.1


class ConflictingCommandsException(Exception, Generic[T]):
    def __init__(self, ctxs: Collection[T]):
        self._ctxs = ctxs
        self._words: list[str] = []

    def prepend_word(self, word: str):
        self._words.insert(0, word)

    def __str__(self):
        return f'Для запроса "{" ".join(self._words)}" добавлено несколько команд:' + \
               ''.join(map(lambda it: f'\n\t- {it}', self._ctxs))


class _CommandTreeNode(Generic[T]):
    def __init__(self):
        self._children: dict[str, _CommandTreeNode] = {}
        self._ctx: Optional[T] = None

    def _get_matches(self, words: Collection[str], tolerance: float, ignore_self=False) \
            -> Generator[_CommandMatch, None, None]:
        if tolerance < 0:
            return

        if len(words) == 0:
            if self._ctx is not None and ignore_self is False:
                yield _CommandMatch(self._ctx, '', tolerance)
            return

        if self._ctx is not None and ignore_self is False:
            yield _CommandMatch(self._ctx, ' '.join(words), tolerance - len(words))

        word, *rest = words

        if word in self._children:
            yield from self._children[word]._get_matches(rest, tolerance)

        # TODO: Добавить нечёткий поиск по частичному совпадению word в self._children

        yield from self._get_matches(rest, tolerance - 1.0, ignore_self=True)

    def get_matches(self, words: Collection[str]) -> Generator[_CommandMatch, None, None]:
        return self._get_matches(words, 2)

    def _add_node_deep(self, first_step=None, *path: Collection[str]) -> '_CommandTreeNode':
        if first_step is None:
            return self

        if first_step not in self._children:
            self._children[first_step] = _CommandTreeNode()

        return self._children[first_step]._add_node_deep(*path)

    def _set_ctx(self, ctx: T):
        if self._ctx is not None:
            raise ConflictingCommandsException([self._ctx, ctx])

        self._ctx = ctx

    def add_dict(self, d: TSrcDict, ctx_constructor: TConstructor):
        for k, v in d.items():
            for k_variant in k.split('|'):
                n = self._add_node_deep(*k_variant.split(' '))

                try:
                    if isinstance(v, dict):
                        n.add_dict(v, ctx_constructor)
                    else:
                        n._set_ctx(ctx_constructor(v))
                except ConflictingCommandsException as e:
                    e.prepend_word(k_variant)
                    raise


class NoCommandMatchesException(Exception):
    def __init__(self, text):
        super().__init__(f'Не удалось подобрать команду для запроса "{text}"')


class AmbiguousCommandException(Exception):
    def __init__(self, text: str, matches: Collection[_CommandMatch]):
        self._text = text
        self._matches = matches

    def __str__(self):
        return f'Не удалось однозначно подобрать команду для запроса "{self._text}". Возможные варианты:' + \
               ''.join(map(lambda it: f'\n\t- {it}', self._matches))


class VACommandTree(Generic[T]):
    """
    Дерево команд.
    Структура данных, хранящая отображение текстовых команд на множество объектов некоторого типа (в основном применении
    дерева такими объектами являются контексты диалога) с реализованными операциями добавления записей и нечёткого
    поиска подходящих объектов по заданному тексту.
    """

    __slots__ = '_root'

    def __init__(self):
        self._root = _CommandTreeNode()

    def add_commands(self, commands: TSrcDict, context_constructor: TConstructor):
        """
        Добавляет команды в дерево.

        Команды представлены в виде словарей произвольной вложенности, где на нижнем уровне вложенности располагается
        значение, из которого затем конструируется объект, хранимый в дереве:

        >>> tree = VACommandTree()
        >>> # Добавит команды "включи свет", "включи звук", "привет"
        >>> tree.add_commands({
        >>>     "включи": {
        >>>         "свет": 'light_on',
        >>>         "звук": 'un_mute',
        >>>     },
        >>>     "привет": 'say_hi'
        >>> }, lambda it: it)

        ключ словаря на любом уровне вложенности может содержать несколько вариантов текста, перечисленные через ``|``:

        >>> # Добавит команды "выключи свет", "отключи свет", "выключи свету", "отключи свету"
        >>> tree.add_commands({
        >>>     "выключи|отключи": {
        >>>         "свет|свету": 'light_off'
        >>>     }
        >>> }, lambda it: it)

        Args:
            commands:
                команды в виде вложенных словарей
            context_constructor:
                функция, преобразующая значение из словаря в значение, хранимое в дереве

        Raises:
            ConflictingCommandsException - если одна из добавляемых команд совпадает с другой добавляемой или ранее
                                           добавленой командой
        """
        self._root.add_dict(commands, context_constructor)

    def get_command(self, text: str) -> Tuple[T, str]:
        """
        Осуществляет поиск наиболее подходящей команды к запросу.

        Args:
            text:
                текст запроса
        Returns:
            кортеж из найденной команды и остатка запроса
        Raises:
            NoCommandMatchesException - если подходящих команд нет
            AmbiguousCommandException - если есть несколько подходящих команд, но выбрать одну однозначно не получается
        """
        words = text.split(' ')
        matching = list(sorted(
            self._root.get_matches(words),
            key=lambda match: match.weight,
            reverse=True,
        ))

        if len(matching) == 0:
            raise NoCommandMatchesException(text)

        best_match = matching[0]

        if len(matching) >= 2 and best_match.weight_is_close_to(matching[1]):
            raise AmbiguousCommandException(
                text,
                list(filter(best_match.weight_is_close_to, matching))
            )

        return best_match.ctx, best_match.text
