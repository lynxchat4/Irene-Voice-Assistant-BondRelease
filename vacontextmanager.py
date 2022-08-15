import logging
from sys import float_info
from threading import Thread, RLock
from time import sleep
from typing import Optional

from vaabstract import VAApi, VAContext

_DEFAULT_TIMEOUT = 10.0
_DEFAULT_TICK_INTERVAL = 1.0


class VAContextManager:
    """
    Менеджер контекста, управляет текущим контекстом диалога.

    Менеджер контекста по сути является конечным автоматом (aka State Machine), в то время как контекст представляет
    собой отдельное состояние с правилами перехода в новые состояния по внешним событиям (получение команды, истечение
    времени ожидания).
    """

    def __init__(self, va: VAApi, default_context: VAContext, default_timeout: float = _DEFAULT_TIMEOUT):
        """
        Args:
            va: экземпляр API голосового ассистента
            default_context: контекст диалога по-умолчанию
            default_timeout: время ожидания следующей команды по-умолчанию. Может быть изменено для отдельного
                контекста (см. метод VAContext.get_timeout) или через поле VAContextManager.default_timeout
        """
        self._va = va
        self._default_context = default_context
        self._current_context = default_context
        self._next_context: Optional[VAContext] = None
        self.default_timeout = default_timeout
        self._timeout = _DEFAULT_TIMEOUT
        self._lck = RLock()

    def set_next_ctx(self, ctx: VAContext):
        """
        При вызове во время выполнения команды или обработки истечения времени ожидания команды назначает следующий
        контекст.

        Игнорируется если метод (handle_command или handle_timeout) текущего контекста возвращает не None.

        Метод добавлен для обратной совместимости (реализации метода context_set).

        Args:
            ctx: контекст, к которому нужно перейти после завершения обработки команды
        """
        self._next_context = ctx

    def _set_ctx(self, ctx: Optional[VAContext]):
        if ctx is None:
            if self._next_context is not None:
                ctx = self._next_context
            else:
                ctx = self._default_context

        self._next_context = None

        self._current_context = ctx

        # не начинать отсчёт времени ожидания до вызова start_timeout
        self._timeout = float_info.max

    def process_command(self, text: str):
        """
        Обрабатывает переданную текстовую команду.

        Args:
            text: текст команды
        """
        with self._lck:
            self._set_ctx(self._current_context.handle_command(self._va, text))

    def start_timeout(self):
        """
        Начинает/перезапускает отсчёт времени ожидания следующей команды.
        """
        with self._lck:
            self._timeout = self._current_context.get_timeout(self.default_timeout)

    def tick_timeout(self, delta: float = 1.0):
        """
        Обрабатывает истечение времени ожидания следующей команды.

        Этот метод должен периодически (раз в delta секунд) вызываться.
        Для этого можно использовать TimeoutTicker.

        Когда команда выполняется, этот метод будет блокировать поток до завершения выполнения команды.
        При этом, время ожидания крайне не желательно включать в значение delta при следующем вызове.

        Args:
            delta: прошедшее время в секундах
        """
        with self._lck:
            self._timeout -= delta

            if self._timeout <= 0:
                self._set_ctx(self._current_context.handle_timeout(self._va))
                self.start_timeout()


class TimeoutTicker(Thread):
    """
    Оповещает менеджер контекста (VAContextManager) течении времени.

    Из-за особенностей работы менеджера контекста, возможна погрешность примерно в (-interval,0) во времени ожидания
    команд.
    Для уменьшения погрешности (если, вдруг, это критично) можно уменьшить interval, однако не слишком сильно, чтобы не
    повредить производительности.
    """

    def __init__(self, cm: VAContextManager, interval: float = _DEFAULT_TICK_INTERVAL):
        """
        Args:
            cm: экземпляр VAContextManager
            interval: интервал оповещения
        """
        super().__init__(daemon=True)
        self._cm = cm
        self._interval = interval

    def run(self) -> None:
        while True:
            sleep(self._interval)

            # noinspection PyBroadException
            try:
                self._cm.tick_timeout(self._interval)
            except Exception:
                logging.exception("Ошибка при обработке истечения времени ожидания команды")
