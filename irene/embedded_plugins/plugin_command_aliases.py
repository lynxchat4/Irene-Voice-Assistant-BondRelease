"""
Добавляет возможность определять собственные псевдонимы для команд, добавленных другими плагинами.
"""

from logging import getLogger
from typing import TypedDict, Union, Optional, Callable

from irene import VAApi
from irene.brain.abc import InboundMessage, VAContext, OutputChannelPool
from irene.brain.command_tree import VACommandTree, NoCommandMatchesException, AmbiguousCommandException, \
    ConflictingCommandsException
from irene.brain.contexts import BaseContextWrapper
from irene.plugin_loader.magic_plugin import step_name, after, before
from irene.utils.metadata import MetadataMapping

name = 'command_aliases'
version = '0.1.0'

_logger = getLogger(name)


class _AliasConfig(TypedDict):
    command: str
    aliases: Union[list[str], str]
    forbid_recursion: bool


class _Config(TypedDict):
    command_aliases: list[_AliasConfig]


config: _Config = {
    'command_aliases': [
        {
            'command': "привет",
            'aliases': "здравствуй|здорова",
            'forbid_recursion': False,
        },
    ],
}

config_comment = """
Настройки псевдонимов команд.

Позволяет назначать собственные фразы для команд, предоставляемых другими плагинами.

Параметры:

- `command_aliases` - список псевдонимов команд. Каждый псевдоним описывается объектом, структура которого описана
                      далее.

Параметры псевдонима:

- `command`           - команда, для которой создаются псевдонимы.
- `aliases`           - список псевдонимов - фраз, которые будут использоваться вместо указанной команды команды.
- `forbid_recursion`  - если `true`, то плагин не будет пытаться определить, является ли команда `command` псевдонимом
                        какой-то другой команды.

Изменения конфигурации применяются без перезапуска приложения.
"""


class _AliasMessage(InboundMessage):
    __slots__ = ('_original', '_text')

    def __init__(self, original: InboundMessage, text: str):
        self._original = original
        self._text = text

    def get_text(self) -> str:
        return self._text

    def get_related_outputs(self) -> OutputChannelPool:
        return self._original.get_related_outputs()

    @property
    def meta(self) -> MetadataMapping:
        return self._original.meta

    def get_original(self) -> InboundMessage:
        return self._original.get_original()


class _Alias:
    __slots__ = ('_command', 'forbid_recursion')

    def __init__(self, alias_config: _AliasConfig):
        self._command = alias_config['command']
        self.forbid_recursion = alias_config.get('forbid_recursion', False)

    def wrap_message(self, message: InboundMessage, rest_text: str) -> InboundMessage:
        full_text = ' '.join((self._command, rest_text)).strip()

        _logger.debug("Применяю псевдоним команды: '%s' -> '%s'", message.get_text(), full_text)

        return _AliasMessage(message, full_text)

    def __str__(self):
        return f"{'нерекурсивный ' if self.forbid_recursion else ''}псевдоним для '{self._command}'"


_tree: Optional[VACommandTree] = None


def _apply_command_aliases(message: InboundMessage) -> InboundMessage:
    if (tree := _tree) is None:
        return message

    applied_aliases: set[_Alias] = set()

    while True:
        try:
            alias, rest = tree.get_command(message.get_text())
        except NoCommandMatchesException:
            return message
        except AmbiguousCommandException as e:
            _logger.warning("Ошибка при разрешении псевдонимов команд: %s", e)
            return message
        else:
            if alias in applied_aliases:
                _logger.warning(
                    "Обнаружен цикл в псевдонимах команд. Останавливаюсь на '%s'",
                    message.get_text(),
                )
                return message

            message = alias.wrap_message(message, rest)
            applied_aliases.add(alias)

            if alias.forbid_recursion:
                return message


class _AliasResolutionContext(BaseContextWrapper):
    def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
        return self._wrapped.handle_command(va, _apply_command_aliases(message))


def receive_config(*_args, **_kwargs) -> None:
    tree: VACommandTree[_Alias] = VACommandTree()

    for alias_conf in config['command_aliases']:
        alias = _Alias(alias_conf)

        aliases_src = alias_conf['aliases']
        aliases: list[str] = [aliases_src] if isinstance(aliases_src, str) else aliases_src

        try:
            tree.add_commands({alias_text: alias for alias_text in aliases}, lambda it: it)
        except ConflictingCommandsException as e:
            _logger.warning("Ошибка при построении списка псевдонимов команд: %s", e)

    global _tree
    _tree = tree


@step_name('apply_command_aliases')
@after('load_commands')
@before('add_trigger_phrase')
def create_root_context(
        nxt: Callable,
        prev: VAContext,
        *args, **kwargs,
):
    return nxt(
        _AliasResolutionContext(prev),
        *args, **kwargs
    )
