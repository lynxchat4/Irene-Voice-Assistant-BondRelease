from argparse import ArgumentParser
from logging import basicConfig, getLogger
from os import environ
from typing import Any

from irene.plugin_loader.magic_plugin import MagicPlugin, after

_DEFAULT_LOG_LEVEL = environ.get('LOG_LEVEL', 'INFO').upper()


class LoggingPlugin(MagicPlugin):
    name = 'logging'
    version = '1.0.0'

    config = {
        'basicConfig': {
            'encoding': 'utf-8',
            'level': _DEFAULT_LOG_LEVEL,
        },
        'levelOverrides': {

        }
    }

    def __init__(self):
        super().__init__()
        basicConfig(level=_DEFAULT_LOG_LEVEL)

    @staticmethod
    def setup_cli_arguments(ap: ArgumentParser, *_args, **_kwargs):
        ap.add_argument(
            '-l', '--log-level',
            help="Уровень логгирования, используемый до загрузки файлов конфигурации",
            dest='log_level',
            metavar="<уровень>",
            type=str,
            default=_DEFAULT_LOG_LEVEL,
        )

    @staticmethod
    def receive_cli_arguments(args: Any, *_args, **_kwargs):
        if args.log_level != _DEFAULT_LOG_LEVEL:
            basicConfig(level=args.log_level, force=True)

    @after('config')
    def bootstrap(self, _pm, *_args, **_kwargs):
        basicConfig(
            **{**self.config.get('basicConfig', {}), **{'force': True}})

        for logger, level in self.config.get('levelOverrides', {}).items():
            getLogger(logger).setLevel(level)
