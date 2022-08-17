import re
from importlib.util import spec_from_file_location, module_from_spec
from os.path import abspath, basename, splitext
from re import Pattern
from typing import Optional, Union, Any
from unittest import TestCase

from irene.active_interaction import construct_active_interaction
from irene.context_manager import VAContextManager
from irene.contexts import construct_context
from irene.va_abc import VAApi, VAContextSource, VAActiveInteractionSource


class _VAApiStub(VAApi):
    ctx_manager: VAContextManager

    def play_audio(self, file_path: str):
        self.say(f'[play {abspath(file_path)}]')

    def submit_active_interaction(self, interaction: VAActiveInteractionSource):
        self.ctx_manager.process_active_interaction(construct_active_interaction(interaction))

    def __init__(self):
        self._output_log = ''

    def say(self, text: str):
        self._output_log = re.sub(r' +', ' ', f'{self._output_log} {text}').strip()

    def pull_output(self) -> str:
        o = self._output_log
        self._output_log = ''
        return o


class DialogTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ctx_manager: Optional[VAContextManager] = None
        self.va = _VAApiStub()

    def using_context(self, ctx: VAContextSource):
        self.ctx_manager = VAContextManager(self.va, construct_context(ctx))
        self.va.ctx_manager = self.ctx_manager
        self.va.pull_output()

    def say(self, text: str):
        if self.ctx_manager is None:
            raise AssertionError(f'метод say("{text}") вызван до using_context()')

        self.ctx_manager.process_command(text)

    def assert_reply(self, pattern: Union[str, Pattern]):
        if self.ctx_manager is None:
            raise AssertionError(f'метод assert_reply("{pattern}") вызван до using_context()')

        reply = self.va.pull_output()

        if re.fullmatch(pattern, reply) is None:
            raise AssertionError(
                f'Ожидался ответ, соответствующий шаблону:\n\t"{pattern}"\n' +
                f'но получен следующий ответ:\n\t"{reply}"' if reply != '' else 'но ответ не получен'
            )

    def delay(self, duration=1.0):
        self.ctx_manager.tick_timeout(duration)

    def play_scenario(self, scenario: str) -> str:
        for ln in scenario.split('\n'):
            line = ln.strip()

            if line == '':
                continue
            elif line[0] == '>':
                self.say(line[1:].strip())
            elif line[0] == '<':
                self.assert_reply(line[1:].strip())
            else:
                raise AssertionError(f'Некорректная строка в тестовом сценарии:\n\t"{line}"')

        return self.va.pull_output()


class PluginDialogTestCase(DialogTestCase):
    plugin: Any = None

    def setUp(self):
        if self.plugin is None:
            raise AssertionError('плагин для тестирования не выбран')

        if isinstance(self.plugin, str):
            spec = spec_from_file_location(
                splitext(basename(self.plugin))[0],
                abspath(self.plugin),
            )
            plugin = module_from_spec(spec)
            spec.loader.exec_module(plugin)
        else:
            plugin = self.plugin

        manifest = plugin.start(self.va)
        self.using_context(manifest.get('commands'))
