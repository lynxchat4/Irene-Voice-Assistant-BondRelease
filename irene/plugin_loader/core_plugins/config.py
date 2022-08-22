import json
from argparse import ArgumentParser
from collections import Collection
from logging import getLogger
from os import environ
from pathlib import Path
from typing import Any, Iterable

import yaml

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from irene.plugin_loader.magic_plugin import MagicPlugin, step_name
from irene.plugin_loader.plugins_abc import PluginManager, OperationStep, Plugin

_CONFIG_EXTENSIONS = ('.yaml', '.yml', '.json')


class ConfigPlugin(MagicPlugin):
    name = 'config'
    version = '1.0.0'

    _logger = getLogger('config')

    config = {
        'yamlDumpOptions': {
            'default_flow_style': False,
            'encoding': 'utf-8',
        },
        'fileEncoding': 'utf-8',
    }
    config_comment = u"""
    Настройки загрузки/сохранения конфигурации.
    """

    def __init__(self):
        super().__init__()

        self._configs: dict[str, dict] = {}
        self._config_comments: dict[str, str] = {}
        self._config_dir: Path = Path('./config')
        self._defaults_dirs: Collection[Path] = []

    @staticmethod
    def setup_cli_arguments(ap: ArgumentParser):
        ap.add_argument(
            '-c', '--config-dir',
            help="Папка, в которой будут храниться файлы конфигурации",
            dest='config_dir',
            metavar='<путь к папке>',
            type=Path,
            default=environ.get('IRENE_CONFIG_DIR', Path.home().joinpath('irene', 'config')),
        )
        ap.add_argument(
            '-d', '--default-config',
            help="Дополнительные папки, в которых находятся файлы конфигурации по-умолчанию",
            dest='default_config_paths',
            metavar='<путь к папке>',
            type=Path,
            default=[],
            action='append',
        )

    def receive_cli_arguments(self, args: Any):
        self._config_dir = args.config_dir
        self._defaults_dirs = args.default_config_paths

    def _get_default_config_files(self, scope: str) -> Iterable[Path]:
        file_names = [scope + ext for ext in _CONFIG_EXTENSIONS]

        for dir_path in self._defaults_dirs:
            for fn in file_names:
                p = dir_path.joinpath(fn)

                if p.is_file():
                    yield p
                    break

    def _get_config_file(self, scope: str) -> Path:
        if not self._config_dir.is_dir():
            if self._config_dir.exists():
                raise Exception(f'Папка конфигурации ({self._config_dir}) существует, но не является папкой.')

            self._config_dir.mkdir(exist_ok=True)

        for ext in _CONFIG_EXTENSIONS[::-1]:
            p = self._config_dir.joinpath(scope + ext)
            if p.is_file():
                return p

        return p

    @staticmethod
    def _load_config_file(p: Path):
        with p.open('r') as f:
            return yaml.load(f, Loader)

    def _get_config(self, scope: str, default: dict) -> dict:
        if scope in self._configs:
            return self._configs[scope]

        main_file = self._get_config_file(scope)

        config = default

        if main_file.is_file():
            config = {**config, **self._load_config_file(main_file)}
        else:
            for default_file in self._get_default_config_files(scope):
                overrides = self._load_config_file(default_file)
                config = {**config, **overrides}

        self._configs[scope] = config

        return config

    def _store_config(self, scope):
        p = self._get_config_file(scope)
        config = self._configs.get(scope, {})

        with p.open('w', encoding=self.config['fileEncoding']) as f:
            if p.suffix == '.json':
                return json.dump(config, f)
            else:
                if scope in self._config_comments:
                    for line in self._config_comments[scope].strip().split('\n'):
                        f.write('# ' + line + '\n')

                return yaml.dump(config, f, Dumper, **self.config['yamlDumpOptions'])

    def _process_plugin_config_steps(self, steps: Iterable[OperationStep]):
        for step in steps:
            if not isinstance(step.step, dict):
                self._logger.warning(
                    "Плагин %s имеет неподдерживаемый тип конфигурации",
                    step.plugin
                )
                continue

            cfg = self._get_config(step.plugin.name, step.step)

            if hasattr(step.plugin, 'config'):
                setattr(step.plugin, 'config', cfg)

            self._config_comments[step.plugin.name] = getattr(
                step.plugin,
                'config_comment',
                f'Настройки плагина {step.plugin}'
            )

    @step_name('config')
    def bootstrap(self, pm: PluginManager):
        self._process_plugin_config_steps(pm.get_operation_sequence('config'))

        for step in pm.get_operation_sequence('receive_config'):
            step.step(self._get_config(step.plugin.name, {}))

        for step in pm.get_operation_sequence('autoconfigure'):
            step.step()

    def plugin_discovered(self, pm: PluginManager, plugin: Plugin):
        self._process_plugin_config_steps(plugin.get_operation_steps('config'))

        for step in plugin.get_operation_steps('receive_config'):
            step.step(self._get_config(step.plugin.name, {}))

        for step in plugin.get_operation_steps('autoconfigure'):
            step.step()

    def terminate(self, pm: PluginManager):
        for scope in self._configs.keys():
            self._store_config(scope)
