import asyncio
import signal
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Collection, Optional, Awaitable

from irene.plugin_loader.abc import Plugin
from irene.plugin_loader.plugin_manager import PluginManagerImpl
from irene.plugin_loader.run_operation import call_all, call_all_parallel_async

_logger = getLogger('launcher')

_HANDLED_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
)


async def _wait_for_interrupt() -> None:
    """
    Возвращает значение при получении приложением сигнала прерывания.

    Task с вызовом этой функции желательно отменить как только слушать сигналы становится не нужно, особенно на Windows.
    """
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def handle_signal(sig, _frame):
        _logger.info("Получен сигнал: %s", signal.Signals(sig).name)
        loop.call_soon_threadsafe(future.set_result, None)

    try:
        for sig in _HANDLED_SIGNALS:
            loop.add_signal_handler(sig, handle_signal, sig, None)
    except NotImplementedError:
        # Код для работы под Windows. Позаимствовано и адаптировано из исходников Uvicorn.
        for sig in _HANDLED_SIGNALS:
            signal.signal(sig, handle_signal)

        # Некоторые библиотеки, например, сервер uvicorn пытаются назначать свои обработчики сигналов, не обращая
        # внимания на обработчики, зарегистрированные ранее.
        # Так что, мы игнорируем то, что они пытаются зарегистрировать вместо наших обработчиков.
        signal_orig = signal.signal

        def _signal(signalnum, handler):
            if signalnum in _HANDLED_SIGNALS:
                _logger.debug(
                    "Обработчик сигнала %s проигнорирован: %s",
                    signal.Signals(signalnum).name,
                    handler
                )
                return None

            return signal_orig(signalnum, handler)

        signal.signal = _signal

        try:
            await future
            return
        finally:
            signal.signal = signal_orig

    await future


async def _run_with_interrupts(future: Awaitable):
    """
    Ждёт завершения переданного Awaitable, одновременно слушая сигналы прерывания.

    Raises:
        InterruptedError
    """
    interrupt_task = asyncio.create_task(_wait_for_interrupt())

    try:
        (completed, *_), __ = await asyncio.wait(
            [future, interrupt_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if completed is interrupt_task:
            raise InterruptedError()
        else:
            await completed
    finally:
        interrupt_task.cancel()


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

    asyncio_debug, executor_max_workers = False, None

    def parse_args(strict: bool):
        ap = ArgumentParser(add_help=strict, prog=canonical_launch_command)

        ap.add_argument(
            '--asyncio-debug',
            action='store_true',
            dest='asyncio_debug',
            help="Включить отладку asyncio",
        )
        ap.add_argument(
            '--executor-max-workers', '-w',
            dest='executor_max_workers',
            metavar='<N>',
            help="Максимальное кол-во потоков в рабочем пуле.",
            default=None,
            required=False,
            type=int,
        )

        call_all(pm.get_operation_sequence('setup_cli_arguments'), ap)

        if strict:
            args = ap.parse_args()
        else:
            args, _ = ap.parse_known_args()

        call_all(pm.get_operation_sequence('receive_cli_arguments'), args)

        nonlocal asyncio_debug, executor_max_workers
        asyncio_debug = args.asyncio_debug
        executor_max_workers = args.executor_max_workers

    parse_args(False)
    call_all(pm.get_operation_sequence('bootstrap'), pm)
    parse_args(True)

    async def run_async_operations():
        executor = ThreadPoolExecutor(
            max_workers=executor_max_workers,
        )
        asyncio.get_running_loop().set_default_executor(executor)

        run_tasks: Optional[Collection[asyncio.Task]] = None

        try:
            init_tasks = await call_all_parallel_async(pm.get_operation_sequence('init'), pm)

            try:
                await _run_with_interrupts(asyncio.gather(*init_tasks))
            except InterruptedError:
                _logger.info("Получен сигнал прерывания в процессе инициализации.")
                return

            _logger.info("Инициализация завершена.")

            run_tasks = await call_all_parallel_async(pm.get_operation_sequence('run'), pm)
            try:
                await _run_with_interrupts(asyncio.gather(*run_tasks))
            except InterruptedError:
                _logger.info("Получен сигнал прерывания.")
                return
            finally:
                for task in run_tasks:
                    task.cancel()
        finally:
            _logger.debug("Начинаю выполнение операции terminate...")

            terminate_tasks = await call_all_parallel_async(pm.get_operation_sequence('terminate'), pm)
            try:
                await _run_with_interrupts(asyncio.gather(*terminate_tasks))
            except InterruptedError:
                _logger.info("Получен ещё один сигнал прерывания. Пытаюсь завершиться быстрее.")
                return

            _logger.debug("Операция terminate завершена.")

            if run_tasks is not None:
                _logger.debug(
                    "Жду завершения задач: %s",
                    [task.get_name() for task in run_tasks if not task.done()]
                )

                if await _run_with_interrupts(asyncio.wait(run_tasks)):
                    _logger.info("Получен ещё один сигнал прерывания. Пытаюсь завершиться быстрее.")
                else:
                    _logger.debug("Все задачи выполнены, завершаюсь штатно.")

    asyncio.run(run_async_operations(), debug=asyncio_debug)
