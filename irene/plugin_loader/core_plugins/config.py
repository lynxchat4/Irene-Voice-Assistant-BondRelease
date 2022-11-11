import json
from argparse import ArgumentParser
from collections import Collection
from logging import getLogger
from os import listdir
from os.path import isdir, isfile, join, basename
from pathlib import Path
from shutil import copyfile
from textwrap import dedent
from threading import Event
from typing import Any, Iterable, Optional

import yaml

from irene.plugin_loader.file_patterns import match_files, first_substitution, substitute_pattern
from irene.plugin_loader.utils.snapshot_hash import snapshot_hash

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from irene.plugin_loader.magic_plugin import MagicPlugin, step_name
from irene.plugin_loader.abc import PluginManager, OperationStep, Plugin

_CONFIG_EXTENSIONS = ('.yaml', '.yml', '.json')

_TEMPLATE_DESCRIPTION_FILE = 'README.txt'

_logger = getLogger('config')


class ConfigurationScope:
    """
    Объект, управляющий состоянием конфигурации отдельного плагина.
    """

    def __init__(
            self,
            main_file_path: Path,
            initial_value: dict[str, Any],
            plugin: Plugin,
            comment: str,
    ):
        self._main_file_path = main_file_path
        self._value = initial_value
        self._plugin = plugin
        self._comment = comment
        self._stored_hash: Optional[int] = None
        self._stored_mtime: Optional[float] = None
        self._notified_hash: Optional[int] = None

    def calc_current_hash(self) -> int:
        return snapshot_hash(self._value)

    def get_current_value(self) -> dict[str, Any]:
        return self._value

    def get_comment(self) -> str:
        return self._comment

    def notify_plugin(self):
        """
        Сообщает плагину если конфигурация была изменена.
        """
        if self._notified_hash == self.calc_current_hash():
            return

        for step in self._plugin.get_operation_steps('receive_config'):
            step.step(self._value)

        # Плагин может изменить конфигурацию в операции receive_config, пересчитываем хеш заново и запоминаем
        self._notified_hash = self.calc_current_hash()

    def was_modified_in_memory(self) -> bool:
        """
        Проверяет, отличается ли конфигурация, хранящаяся в памяти от той, которая была в последний раз прочитана из
        основного файла конфигурации.

        Если конфигурация ранее не была прочитана из основного файла конфигурации, то возвращается True.
        """
        return self._stored_hash != self.calc_current_hash()

    def exists_on_disk(self):
        return self._main_file_path.exists()

    def was_modified_on_disk(self) -> bool:
        """
        Проверяет, был ли файл на диске изменён с последней загрузки.

        "Изменение" включает удаление существующего файла или создание не существовавшего файла.
        """
        if self._main_file_path.exists() != (self._stored_mtime is not None):
            return True

        if self._stored_mtime is not None:
            return self._main_file_path.stat().st_mtime > self._stored_mtime

        return False

    def apply_patch(self, patch: dict[str, Any]):
        for k, v in patch.items():
            self._value[k] = v

    def load_file(self, file_path: Path, encoding: str) -> dict[str, Any]:
        """
        Загружает значения из заданного файла в текущее значение конфигурации.

        Args:
            file_path:
                Путь к файлу конфигурации
            encoding:
                Кодировка файла
        Returns:
            Словарь со значениями, прочитанными из файла.
        """
        try:
            with file_path.open('r', encoding=encoding) as f:
                data = yaml.load(f, Loader)
        except Exception as e:
            _logger.exception(f"Ошибка при чтении файла конфигурации {file_path}", exc_info=e)
            raise Exception(f"Не удалось прочитать файл конфигурации {file_path}") from None

        if not isinstance(data, dict):
            raise Exception(f"Файл конфигурации {file_path} содержит что-то неожиданное вместо одного объекта")

        self.apply_patch(data)

        return data

    def load_main_file(self, encoding: str):
        """
        Загружает главный файл конфигурации из файловой системы.
        """
        if self._main_file_path.exists():
            loaded_data = self.load_file(self._main_file_path, encoding)

            self._stored_hash = snapshot_hash(loaded_data)
            self._stored_mtime = self._main_file_path.stat().st_mtime
        else:
            self._stored_hash = None
            self._stored_mtime = None

    def store_main_file(self, encoding: str, yaml_options: dict[str, Any]):
        """
        Сохраняет текущее значение конфигурации в главный файл конфигурации.
        """
        with self._main_file_path.open('w', encoding=encoding) as f:
            if self._main_file_path.suffix == '.json':
                json.dump(self._value, f)
            else:
                for line in self._comment.strip().split('\n'):
                    f.write('# ' + line + '\n')
                yaml.dump(self._value, f, Dumper, **yaml_options)

        self._stored_mtime = self._main_file_path.stat().st_mtime


class ConfigPlugin(MagicPlugin):
    name = 'config'
    version = '1.0.0'

    config: dict[str, Any] = {
        'yamlDumpOptions': {
            'default_flow_style': False,
            'encoding': 'utf-8',
            'allow_unicode': True,
        },
        'fileEncoding': 'utf-8',
        'storeOnRESTUpdate': True,
        'storeOnShutdown': True,
        'watchFileChanges': True,
        'watchMemoryChanges': True,
        'watchIntervalSeconds': 30,
    }
    config_comment = u"""
    Настройки загрузки, сохранения и обновления конфигурации.

    Доступны следующие параметры:

    - `yamlDumpOptions` - параметры, передаваемые функции `yaml.dump` см. https://pyyaml.org/wiki/PyYAMLDocumentation
    - `storeOnRESTUpdate` - если True, то конфигурация автоматически сохраняется в файл при её обновлении через REST API
    - `storeOnShutdown` - если True, то конфигурация сохраняется при завершении работы.
      Сохранение при завершении работы срабатывает не всегда.
    - `watchFileChanges` - если True, то загрузчик конфигурации будет проверять, изменились ли файлы конфигурации на
      диске и загружать их в случае изменений.
      Для полноценного применения некоторых настроек может всё ещё понадобиться перезапуск приложения.
    - `watchMemoryChanges` - если True, то загрузчик конфигурации будет отслеживать изменения конфигурации, хранящейся в
      памяти и записывать её актуальное состояние в файл.
    - `watchIntervalSeconds` - интервал времени в секундах, через который загрузчик конфигурации проверяет наличие
      изменений файлов конфигурации (`watchFileChanges`) и хранимой в памяти конфигурации (`watchMemoryChanges`).

    Если установлены одновременно флаги `watchFileChanges` и `watchMemoryChanges`, то при одновременном (в течение
    одного интервала `watchIntervalSeconds`) изменении конфигурации и в памяти и в файле на диске приоритет имеют
    изменения внесённые в памяти и, соответственно, файл конфигурации будет перезаписан.
    """

    def __init__(self, *, template_paths: Collection[str] = ()):
        super().__init__()

        self._scopes: dict[str, ConfigurationScope] = {}
        self._config_dir: Path = Path('./config')
        self._defaults_dirs: Collection[Path] = []
        self._template_paths = template_paths
        self._template_extracted = False
        self._watch_termination_request = Event()
        self._watch_terminated = Event()

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
            type=str,
            default='{irene_home}/config',
        )
        ap.add_argument(
            '-d', '--default-config',
            help="Дополнительные папки, в которых находятся файлы конфигурации по-умолчанию",
            dest='default_config_paths',
            metavar='<путь к папке>',
            type=str,
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
        self._config_dir = Path(first_substitution(args.config_dir))
        self._defaults_dirs = [Path(it) for pattern in args.default_config_paths for it in substitute_pattern(pattern)]

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

    def _get_file_encoding(self) -> str:
        return self.config.get('fileEncoding', 'utf-8')

    def _init_config_scope(self, config_step: OperationStep):
        if isinstance(config_step.step, dict):
            config_value = config_step.step
        else:
            _logger.warning(
                "Плагин %s имеет неподдерживаемый тип конфигурации",
                config_step.plugin
            )
            return

        comment = dedent(getattr(
            config_step.plugin,
            'config_comment',
            f'Настройки плагина {config_step.plugin}'
        ))

        main_file_path = self._get_config_file(config_step.plugin.name)

        scope = ConfigurationScope(
            main_file_path,
            config_value,
            config_step.plugin,
            comment,
        )

        for defaults_path in self._get_default_config_files(config_step.plugin.name):
            if defaults_path.exists():
                scope.load_file(defaults_path, self._get_file_encoding())

        if scope.exists_on_disk():
            scope.load_main_file(self._get_file_encoding())

        scope.notify_plugin()

        if scope.was_modified_in_memory():
            scope.store_main_file(
                self._get_file_encoding(),
                yaml_options=self.config['yamlDumpOptions']
            )

        self._scopes[config_step.plugin.name] = scope

    def _store_config(self, scope_name):
        try:
            scope = self._scopes[scope_name]
        except KeyError:
            _logger.warning(
                "0.o Попытка сохранить несуществующую конфигурацию %s",
                scope_name,
            )
            return

        if scope.exists_on_disk() and scope.was_modified_on_disk():
            _logger.debug(
                "Похоже, файл конфигурации для %s был изменён на диске. Не буду перезаписывать его.",
                scope_name,
            )
            return

        if not scope.was_modified_in_memory():
            _logger.debug(
                "Конфигурация %s не была изменена. Не буду перезаписывать файл.",
                scope_name,
            )
            return

        scope.store_main_file(
            self.config.get('encoding', 'utf-8'),
            yaml_options=self.config.get('yamlDumpOptions', {})
        )

    @step_name('config')
    def bootstrap(self, pm: PluginManager, *_args, **_kwargs):
        for step in pm.get_operation_sequence('config'):
            self._init_config_scope(step)

    def plugin_discovered(self, _pm: PluginManager, plugin: Plugin, *_args, **_kwargs):
        for step in plugin.get_operation_steps('config'):
            self._init_config_scope(step)

    def run(self, *_args, **_kwargs):
        try:
            while not self._watch_termination_request.wait(self.config['watchIntervalSeconds']):
                watch_file_changes, watch_memory_changes = \
                    self.config['watchFileChanges'], self.config['watchMemoryChanges']

                if (not watch_file_changes) and (not watch_memory_changes):
                    continue

                for scope_name, scope in self._scopes.items():
                    if watch_memory_changes and scope.was_modified_in_memory():
                        _logger.info(
                            "Конфигурация для %s была изменена, перезаписываю файл",
                            scope_name,
                        )
                        try:
                            scope.store_main_file(self._get_file_encoding(), self.config['yamlDumpOptions'])
                        except Exception:
                            _logger.exception("Ошибка при сохранении конфигурации для %s", scope_name)
                    elif watch_file_changes and scope.was_modified_on_disk():
                        _logger.info(
                            "Файл конфигурации для %s был изменён, загружаю его",
                            scope_name,
                        )
                        try:
                            scope.load_main_file(self._get_file_encoding())
                        except Exception:
                            _logger.exception("Ошибка при загрузке конфигурации для %s", scope_name)

                        try:
                            scope.notify_plugin()
                        except Exception:
                            _logger.exception("Ошибка при обработке изменений в конфигурации %s", scope_name)
        finally:
            self._watch_terminated.set()

    def terminate(self, *_args, **_kwargs):
        self._watch_termination_request.set()
        self._watch_terminated.wait()
        self._watch_terminated.clear()
        self._watch_termination_request.clear()

        if self.config['storeOnShutdown']:
            for scope_name in self._scopes.keys():
                self._store_config(scope_name)

    def register_fastapi_endpoints(self, router, *_args, **_kwargs):
        from fastapi import APIRouter, Body, HTTPException
        from pydantic import BaseModel, Field

        r: APIRouter = router

        class ConfigModel(BaseModel):
            scope: str = Field(
                title="Имя конфига",
                description="Как правило, совпадает с именем плагина, которому принадлежит конфиг",
            )
            config: dict[str, Any] = Field(
                title="Текущее состояние конфига",
            )
            comment: Optional[str] = Field(
                title="Дополнительный комментарий о настройке плагина",
            )

        @r.get(
            '/configs',
            response_model=list[ConfigModel],
            name="Получение всех конфигов",
        )
        def get_all_configs() -> list[ConfigModel]:
            """
            Возвращает список всех конфигов с их текущим состоянием.
            """
            return list(
                sorted(
                    (ConfigModel(
                        scope=scope_name,
                        config=scope.get_current_value(),
                        comment=scope.get_comment(),
                    ) for scope_name, scope in self._scopes.items()),
                    key=lambda conf: conf.scope
                )
            )

        @r.get(
            '/configs/{scope_name}',
            response_model=ConfigModel,
            name="Получение одного конфига",
        )
        def get_one_config(scope_name: str) -> ConfigModel:
            """
            Возвращает один конфиг.
            """
            try:
                scope = self._scopes[scope_name]
            except KeyError:
                raise HTTPException(404)

            return ConfigModel(
                scope=scope_name,
                config=scope.get_current_value(),
                comment=scope.get_comment(),
            )

        @r.patch(
            '/configs/{scope_name}',
            name="Обновление одного конфига",
        )
        def update_scope_config(scope_name: str, config: dict[str, Any] = Body()):
            """
            Обновляет один из конфигов.

            Значения из переданного документа записываются в текущее состояние конфига заменяя имеющиеся значения.
            Если какие-то поля отсутствуют в переданном документе, то значения в текущем состоянии останутся
            неизменными.

            В некоторых случаях изменения могут повлиять на работу плагинов сразу же, иногда может понадобиться
            перезапуск приложения.
            """
            try:
                scope = self._scopes[scope_name]
            except KeyError:
                raise HTTPException(404)

            scope.apply_patch(config)
            scope.notify_plugin()

            if self.config['storeOnRESTUpdate']:
                self._store_config(scope_name)
