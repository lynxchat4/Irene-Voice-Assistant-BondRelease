from functools import partial
from typing import Any, Optional, Callable, TypedDict, Literal

from irene import VAContext, VAApiExt, construct_context, VAContextSource
from irene.brain.brain import BrainImpl
from irene.brain.command_tree import VACommandTree
from irene.brain.contexts import CommandTreeContext, UNKNOWN_COMMAND_SPECIAL_KEY, AMBIGUOUS_COMMAND_SPECIAL_KEY, \
    TriggerPhraseContext
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, step_name, operation, after, before
from irene.plugin_loader.run_operation import call_all_as_wrappers


class BrainPlugin(MagicPlugin):
    name = 'brain'
    version = '1.0.1'

    class _Config(TypedDict):
        triggerPhrases: list[str]
        unknownRootCommandReply: str
        ambiguousRootCommandReply: str
        unknownCommandReply: str
        ambiguousCommandReply: str
        defaultTimeout: float
        timeoutCheckInterval: float
        timeoutsDisabled: bool

    config: _Config = {
        'triggerPhrases': ["ирина", "ирины", "ирину"],
        'unknownRootCommandReply': "Извини, я не поняла",
        'ambiguousRootCommandReply': "Извини, я не совсем поняла",
        'unknownCommandReply': "Не поняла...",
        'ambiguousCommandReply': "Не совсем поняла...",
        'defaultTimeout': 10.0,
        'timeoutsDisabled': False,
        'timeoutCheckInterval': 1.0,
    }

    _ErrorPhraseKeys = Literal['unknownRootCommandReply',
    'ambiguousRootCommandReply']

    def __init__(self):
        super().__init__()

        self._brain: Optional = None

    def _construct_context(self, pm: PluginManager, src: VAContextSource, **kwargs):
        if 'construct_nested' not in kwargs:
            kwargs['construct_nested'] = partial(self._construct_context, pm)

        context = call_all_as_wrappers(
            pm.get_operation_sequence('construct_context'),
            src,
            pm,
            **kwargs
        )

        if not isinstance(context, VAContext):
            raise Exception(f"Не удалось создать контекст из {src}")

        return context

    @operation('construct_context')
    @step_name('add_default_unknown_command_handlers')
    @before('construct_default')
    def add_default_unknown_command_handlers(
            self,
            nxt: Callable,
            prev: VAContextSource,
            pm: PluginManager,
            *args, **kwargs
    ):
        """
        Добавляет обработчики по-умолчанию для нераспознанных команд ко всем контекстам, конструируемым из словарей.

        Если обработчики уже есть, то они не меняются.
        """
        if not isinstance(prev, dict):
            return nxt(prev, pm, *args, **kwargs)

        if UNKNOWN_COMMAND_SPECIAL_KEY in prev and AMBIGUOUS_COMMAND_SPECIAL_KEY in prev:
            return nxt(prev, pm, *args, **kwargs)

        context: Optional[VAContext] = None

        def error_ctx(phrase_name: BrainPlugin._ErrorPhraseKeys, va: VAApiExt, text: str):
            self._say_configured(phrase_name, va, text)
            if context is not None:
                va.context_set(context)

        prev = prev.copy()

        if UNKNOWN_COMMAND_SPECIAL_KEY not in prev:
            prev[UNKNOWN_COMMAND_SPECIAL_KEY] = partial(
                error_ctx, 'unknownCommandReply')

        if AMBIGUOUS_COMMAND_SPECIAL_KEY not in prev:
            prev[AMBIGUOUS_COMMAND_SPECIAL_KEY] = partial(
                error_ctx, 'ambiguousCommandReply')

        context = nxt(prev, pm, *args, **kwargs)
        return context

    @step_name('construct_default')
    def construct_context(
            self,
            nxt: Callable,
            prev: VAContextSource,
            *args, **kwargs
    ):
        """
        Создаёт контекст из исходного объекта используя функцию ``construct_context``.
        """
        return nxt(construct_context(prev, **kwargs), *args, **kwargs)

    @step_name('create_brain')
    def init(self, pm: PluginManager):
        """
        Создаёт основной экземпляр Мозга.
        """
        root_ctx: VAContext = call_all_as_wrappers(
            pm.get_operation_sequence('create_root_context'), None, pm)
        self._brain = BrainImpl(
            main_context=root_ctx,
            config=self.config,
            context_constructor=partial(self._construct_context, pm),
        )

    @step_name('kill_brain')
    def terminate(self, *_):
        """
        Уничтожает основной экземпляр Мозга.
        """
        if self._brain:
            try:
                self._brain.kill()
            finally:
                self._brain = None

    @step_name('default_brain')
    def get_brain(self, nxt, prev, *args, **kwargs):
        """
        Возвращает основной экземпляр Мозга, если другой экземпляр не был предоставлен предыдущими шагами.
        """
        return nxt(prev or self._brain, *args, **kwargs)

    def _say_configured(self, key: _ErrorPhraseKeys, va: VAApiExt, _: str):
        va.say(self.config[key])

    @operation('create_root_context')
    @step_name('load_commands')
    def create_root_context(
            self,
            nxt: Callable,
            prev: Optional[VAContext],
            pm: PluginManager,
            *args, **kwargs
    ):
        """
        Создаёт корневой контекст, добавляя в него все команды, предоставляемые плагинами.

        Если другой корневой контекст был создан до этого шага, то ему будут переданы все нераспознанные команды.
        Иначе на нераспознанные команды ассистент будет отвечать настроенными фразами.
        """
        tree: VACommandTree[VAContext] = VACommandTree()

        unknown_command_context = prev or partial(
            self._say_configured, 'unknownRootCommandReply')
        ambiguous_command_context = partial(
            self._say_configured, 'ambiguousRootCommandReply')

        context_constructor = partial(self._construct_context, pm)

        def add_commands(commands: dict[str, Any]):
            nonlocal unknown_command_context, ambiguous_command_context

            if UNKNOWN_COMMAND_SPECIAL_KEY in commands:
                commands = commands.copy()
                unknown_command_context = commands.pop(
                    UNKNOWN_COMMAND_SPECIAL_KEY)

            if AMBIGUOUS_COMMAND_SPECIAL_KEY in commands:
                commands = commands.copy()
                ambiguous_command_context = commands.pop(
                    AMBIGUOUS_COMMAND_SPECIAL_KEY)

            tree.add_commands(commands, context_constructor)

        for step in pm.get_operation_sequence('define_commands'):
            definition = step.step

            while True:
                if definition is None:
                    break
                elif isinstance(definition, dict):
                    add_commands(definition)
                    break
                elif callable(definition):
                    definition = definition()
                    continue
                else:
                    raise TypeError(
                        f"Неподдерживаемый тип определения команд в плагине {step.plugin} ({step}): {type(definition)}"
                    )

        return nxt(
            CommandTreeContext(
                tree,
                context_constructor(unknown_command_context),
                context_constructor(ambiguous_command_context)
            ),
            *args, **kwargs
        )

    @operation('create_root_context')
    @step_name('add_trigger_phrase')
    @after('load_commands')
    def add_trigger_phrase(
            self,
            nxt: Callable,
            prev: Optional[VAContext],
            *args, **kwargs,
    ):
        """
        Заворачивает корневой контекст в ``TriggerPhraseContext``, требующий наличия настроенной фразы во входящем
        сообщении для обработки сообщения.
        """
        if prev is None:
            raise ValueError()

        return nxt(
            TriggerPhraseContext(
                [phrase.split(' ')
                 for phrase in self.config['triggerPhrases']],
                prev,
            ),
            *args, **kwargs
        )
