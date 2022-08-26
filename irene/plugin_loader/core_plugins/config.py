import json
from argparse import ArgumentParser
from collections import Collection
from logging import getLogger
from os import environ, listdir
from os.path import isdir, isfile, join, basename
from pathlib import Path
from shutil import copyfile
from typing import Any, Iterable

import yaml

from irene.plugin_loader.file_match import match_files

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from irene.plugin_loader.magic_plugin import MagicPlugin, step_name
from irene.plugin_loader.abc import PluginManager, OperationStep, Plugin

_CONFIG_EXTENSIONS = ('.yaml', '.yml', '.json')

_TEMPLATE_DESCRIPTION_FILE = 'README.txt'


class ConfigPlugin(MagicPlugin):
    name = 'config'
    version = '1.0.0'

    _logger = getLogger('config')

    config: dict[str, Any] = {
        'yamlDumpOptions': {
            'default_flow_style': False,
            'encoding': 'utf-8',
            'allow_unicode': True,
        },
        'fileEncoding': 'utf-8',
    }
    config_comment = u"""
    Настройки загрузки/сохранения конфигурации.
    """

    def __init__(self, *, template_paths: Collection[str] = ()):
        super().__init__()

        self._configs: dict[str, dict] = {}
        self._config_comments: dict[str, str] = {}
        self._config_dir: Path = Path('./config')
        self._defaults_dirs: Collection[Path] = []
        self._template_paths = template_paths
        self._template_extracted = False

    def setup_cli_arguments(self, ap: ArgumentParser, *_args, **_kwargs):
        if len(self._template_paths) > 0:
            ap.add_argument(
                '-T', '--config-template',
                help="Имя шаблона конфигурации. "
                     "Если аргумент передан и шаблон с таким именем существует, то файлы конфигурации из шаблона "
                     "заменят текущие файлы конфигурации. "
                     "Полезно для первоначальной настройки.",
                dest='config_template_name',
                metavar='<имя шаблона>',
                type=str,
                default=None,
            )
            ap.add_argument(
                '-L', '--list-config-templates',
                help="Перечисляет доступные шаблоны конфигурации",
                dest='list_config_templates',
                action='store_const',
                const=True,
                default=False,
            )
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

    def _get_template_paths(self, template_name):
        return [
            p
            for p in match_files(join(p, template_name) for p in self._template_paths)
            if isdir(p) and isfile(join(p, _TEMPLATE_DESCRIPTION_FILE))
        ]

    def _list_templates(self):
        paths = self._get_template_paths('*')

        if len(paths) == 0:
            print(match_files(self._template_paths))
            print("Нет доступных шаблонов конфигурации")
            return

        for p in paths:
            print(f'{basename(p)}:')

            with open(join(p, _TEMPLATE_DESCRIPTION_FILE), 'r', encoding='utf-8') as file:
                for line in file:
                    print(f'\t{line}')

    def _ensure_config_dir(self):
        if not self._config_dir.is_dir():
            if self._config_dir.exists():
                raise Exception(f'Папка конфигурации ({self._config_dir}) существует, но не является папкой.')

            self._config_dir.mkdir(exist_ok=True, parents=True)

    def _extract_template(self, template):
        if self._template_extracted:
            return
        self._template_extracted = True

        templates = self._get_template_paths(template)

        if len(templates) == 0:
            print(f"Не удалось найти шаблон конфигурации {template}")
            exit(1)

        self._ensure_config_dir()

        print(f"Копирую конфигурацию из шаблона {template}...")

        template_path = templates[0]

        for fn in listdir(template_path):
            if fn == _TEMPLATE_DESCRIPTION_FILE:
                continue

            dst_path = self._config_dir.joinpath(fn)

            if dst_path.is_file():
                print(f"Файл {dst_path} существует, он будет заменён файлом из шаблона {template}")

            copyfile(join(template_path, fn), dst_path)

    def receive_cli_arguments(self, args: Any, *_args, **_kwargs):
        self._config_dir = args.config_dir
        self._defaults_dirs = args.default_config_paths

        if len(self._template_paths) > 0:
            if args.list_config_templates:
                self._list_templates()
                exit(0)

            if args.config_template_name is not None:
                self._extract_template(args.config_template_name)

    def _get_default_config_files(self, scope: str) -> Iterable[Path]:
        file_names = [scope + ext for ext in _CONFIG_EXTENSIONS]

        for dir_path in self._defaults_dirs:
            for fn in file_names:
                p = dir_path.joinpath(fn)

                if p.is_file():
                    yield p
                    break

    def _get_config_file(self, scope: str) -> Path:
        self._ensure_config_dir()

        for ext in _CONFIG_EXTENSIONS[::-1]:
            p = self._config_dir.joinpath(scope + ext)
            if p.is_file():
                return p

        return p

    def _load_config_file(self, p: Path):
        try:
            with p.open(
                    'r',
                    encoding=self.config.get('fileEncoding', 'utf-8'),
            ) as f:
                return yaml.load(f, Loader)
        except Exception as e:
            self._logger.exception(f"Ошибка при чтении файла конфигурации {p}", exc_info=e)
            raise Exception(f"Не удалось прочитать файл конфигурации {p}") from None

    def _get_config(self, scope: str, default: dict) -> dict:
        if scope in self._configs:
            return self._configs[scope]

        main_file = self._get_config_file(scope)

        config = default

        if main_file.is_file():
            from_file = self._load_config_file(main_file)
            config = {**config, **from_file}
        else:
            for default_file in self._get_default_config_files(scope):
                try:
                    overrides = self._load_config_file(default_file)
                except Exception:
                    pass
                else:
                    config = {**config, **overrides}

        self._configs[scope] = config

        return config

    def _store_config(self, scope):
        p = self._get_config_file(scope)
        config = self._configs.get(scope, {})

        with p.open('w', encoding=self.config.get('fileEncoding', 'utf-8')) as f:
            if p.suffix == '.json':
                return json.dump(config, f)
            else:
                if scope in self._config_comments:
                    for line in self._config_comments[scope].strip().split('\n'):
                        f.write('# ' + line.strip() + '\n')

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
    def bootstrap(self, pm: PluginManager, *_args, **_kwargs):
        self._process_plugin_config_steps(pm.get_operation_sequence('config'))

        for step in pm.get_operation_sequence('receive_config'):
            step.step(self._get_config(step.plugin.name, {}))

    def plugin_discovered(self, pm: PluginManager, plugin: Plugin, *_args, **_kwargs):
        self._process_plugin_config_steps(plugin.get_operation_steps('config'))

        for step in plugin.get_operation_steps('receive_config'):
            step.step(self._get_config(step.plugin.name, {}))

    def terminate(self, pm: PluginManager, *_args, **_kwargs):
        for scope in self._configs.keys():
            self._store_config(scope)
