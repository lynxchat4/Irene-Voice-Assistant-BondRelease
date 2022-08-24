from functools import partial
from typing import Any, Optional, Callable

from irene import VAContext, VAApiExt, construct_context
from irene.brain.brain import BrainImpl
from irene.brain.command_tree import VACommandTree
from irene.brain.contexts import CommandTreeContext, UNKNOWN_COMMAND_SPECIAL_KEY, AMBIGUOUS_COMMAND_SPECIAL_KEY, \
    TriggerPhraseContext
from irene.plugin_loader.magic_plugin import MagicPlugin, step_name, operation, after
from irene.plugin_loader.plugins_abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers


class BrainPlugin(MagicPlugin):
    name = 'brain'
    version = '1.0.0'

    config = {
        'triggerPhrases': ["ирина", "ирины", "ирину"],
        'unknownRootCommandReply': "Извини, я не поняла",
        'ambiguousRootCommandReply': "Извини, я не совсем поняла",
    }

    def __init__(self):
        super().__init__()

        self._brain: Optional = None

    @step_name('create_brain')
    def init(self, pm: PluginManager):
        root_ctx: VAContext = call_all_as_wrappers(pm.get_operation_sequence('create_root_context'), None, pm)
        self._brain = BrainImpl(
            main_context=root_ctx,
            config=self.config,
        )

    @step_name('kill_brain')
    def terminate(self, *_):
        if self._brain:
            self._brain.kill()

    @step_name('default_brain')
    def get_brain(self, prev, nxt, *__):
        return nxt(prev or self._brain)

    def _say_configured(self, key: str, va: VAApiExt, _: str):
        va.say(self.config[key])

    @operation('create_root_context')
    @step_name('load_commands')
    def create_root_context(
            self,
            prev: Optional[VAContext],
            nxt: Callable[[VAContext], VAContext],
            pm: PluginManager
    ):
        tree: VACommandTree[VAContext] = VACommandTree()

        unknown_command_context = prev or partial(self._say_configured, 'unknownRootCommandReply')
        ambiguous_command_context = partial(self._say_configured, 'ambiguousRootCommandReply')

        def add_commands(commands: dict[str, Any]):
            nonlocal unknown_command_context, ambiguous_command_context

            if UNKNOWN_COMMAND_SPECIAL_KEY in commands:
                commands = commands.copy()
                unknown_command_context = commands.pop(UNKNOWN_COMMAND_SPECIAL_KEY)

            if AMBIGUOUS_COMMAND_SPECIAL_KEY in commands:
                commands = commands.copy()
                ambiguous_command_context = commands.pop(AMBIGUOUS_COMMAND_SPECIAL_KEY)

            tree.add_commands(commands, construct_context)

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

        return nxt(CommandTreeContext(
            tree,
            construct_context(unknown_command_context),
            construct_context(ambiguous_command_context)
        ))

    @operation('create_root_context')
    @after('load_commands')
    def add_trigger_phrase(
            self,
            prev: Optional[VAContext],
            nxt: Callable[[VAContext], VAContext],
            pm: PluginManager,
    ):
        if prev is None:
            raise ValueError()

        return nxt(TriggerPhraseContext(
            [phrase.split(' ') for phrase in self.config['triggerPhrases']],
            prev,
        ))
