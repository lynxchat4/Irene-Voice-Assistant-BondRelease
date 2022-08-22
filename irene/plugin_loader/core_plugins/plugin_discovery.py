from collections import Iterable
from importlib.util import spec_from_file_location, module_from_spec
from inspect import isclass
from logging import getLogger
from os.path import isfile, basename, splitext
from types import ModuleType
from typing import Optional

from irene.plugin_loader.file_match import match_files
from irene.plugin_loader.magic_plugin import MagicPlugin, after, step_name
from irene.plugin_loader.plugins_abc import PluginManager, Plugin, OperationStep
from irene.plugin_loader.run_operation import call_until_first_result, call_all


class PluginDiscoveryPlugin(MagicPlugin):
    name = 'discover_plugins'
    version = '1.0.0'

    _logger = getLogger('discover_plugins')

    config = {
        'pluginPaths': [
            "{irene_path}/embedded_plugins/plugin_*.py",
            "{user_home}/irene-plugins/plugin_*.py",
            "{python_path}/irene-plugin-*/plugin_*.py",
        ],
        "excludePlugins": []
    }

    def __init__(self):
        super().__init__()
        self._plugins: list[Plugin] = []
        self._excluded: set[str] = set()

    def receive_config(self, config):
        self._excluded = set(config['excludePlugins'])

    def get_operation_steps(self, op_name: str) -> Iterable[OperationStep]:
        for plugin in self._plugins:
            yield from plugin.get_operation_steps(op_name)

        yield from super().get_operation_steps(op_name)

    @after('config')
    def bootstrap(self, pm: PluginManager):
        plugin_discover_op = list(pm.get_operation_sequence('discover_plugins_at_path'))
        plugin_discovered_op = list(pm.get_operation_sequence('plugin_discovered'))

        for plugin_path in match_files(self.config['pluginPaths']):
            plugins: Optional[Iterable[Plugin]] = call_until_first_result(plugin_discover_op, pm, plugin_path)

            if plugins is None:
                self._logger.warning(
                    "Не удалось загрузить плагин из %s",
                    plugin_path
                )
                continue

            for plugin in plugins:
                if plugin.name in self._excluded or str(plugin) in self._excluded:
                    continue

                self._logger.debug(
                    "Найден плагин %s в файле %s",
                    plugin, plugin_path
                )

                self._plugins.append(plugin)
                call_all(plugin_discovered_op, pm, plugin)

    @step_name('discover_python_module')
    def discover_plugins_at_path(self, pm: PluginManager, path: str):
        if not isfile(path):
            return

        if not path.endswith('.py'):
            return

        module_name = splitext(basename(path))[0]

        if module_name in self._excluded:
            return

        spec = spec_from_file_location(
            module_name,
            path,
        )

        if spec is None or spec.loader is None:
            self._logger.warning(
                "Не удалось загрузить модуль плагина %s - не удалось создать спецификацию модуля",
                path
            )
            return

        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        return call_until_first_result(pm.get_operation_sequence('discover_plugins_in_module'), pm, module)

    @step_name('discover_explicit_plugins')
    def discover_plugins_in_module(self, pm: PluginManager, module: ModuleType):
        found = []
        attrs = getattr(module, '__all__', dir(module))

        for attr in attrs:
            value = getattr(module, attr, None)

            if isinstance(value, Plugin):
                found.append(value)
            elif isclass(value) and \
                    issubclass(value, Plugin) and \
                    getattr(value, '__module__', module.__name__) == module.__name__:
                if getattr(value, 'name', None) in self._excluded:
                    continue

                found.append(value())

        if len(found) > 0:
            return found
