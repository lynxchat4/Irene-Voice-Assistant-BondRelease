from argparse import ArgumentParser
from collections import Collection

from irene.plugin_loader.plugin_manager import PluginManagerImpl
from irene.plugin_loader.plugins_abc import Plugin
from irene.plugin_loader.run_operation import call_all, call_all_failsafe


def launch_application(
        core_plugins: Collection[Plugin],
        *,
        canonical_launch_command=None
):
    """
    Запускает приложение с заданным набором плагинов ядра.

    Args:
        core_plugins:
            коллекция плагинов ядра
        canonical_launch_command:
            имя команды, используемой для запуска приложения (используется для вывода справки)
    """
    pm = PluginManagerImpl(core_plugins)

    def parse_args(strict: bool):
        ap = ArgumentParser(add_help=strict, prog=canonical_launch_command)
        call_all(pm.get_operation_sequence('setup_cli_arguments'), ap)

        if strict:
            args = ap.parse_args()
        else:
            args, _ = ap.parse_known_args()

        call_all(pm.get_operation_sequence('receive_cli_arguments'), args)

    parse_args(False)
    call_all(pm.get_operation_sequence('bootstrap'), pm)
    parse_args(True)

    try:
        call_all(pm.get_operation_sequence('init'), pm)

        call_all(pm.get_operation_sequence('run'), pm)
    finally:
        call_all_failsafe(pm.get_operation_sequence('terminate'), pm)
