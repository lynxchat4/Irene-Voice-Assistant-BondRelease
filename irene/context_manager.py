import logging
from threading import Thread, Lock, Event
from typing import Optional

from .contexts import InterruptContext
from .va_abc import VAApi, VAContext, VAActiveInteraction, InboundMessage

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
        self.default_timeout = default_timeout
        self._timeout = _DEFAULT_TIMEOUT
        self._lck = Lock()

    def _set_ctx(self, ctx: Optional[VAContext]):
        if ctx is None:
            ctx = self._default_context

        self._current_context = ctx
        self._start_timeout()

    def process_command(self, message: InboundMessage):
        """
        Обрабатывает переданную текстовую команду.

        Args:
            message: сообщение от пользователя
        """
        with self._lck:
            self._set_ctx(self._current_context.handle_command(self._va, message))

    def process_active_interaction(self, interaction: VAActiveInteraction):
        """
        Выполняет активное взаимодействие.

        Args:
            interaction:
        """
        with self._lck:
            interrupted: Optional[VAContext] = self._current_context.handle_interrupt(self._va)

            interrupting: Optional[VAContext] = None

            try:
                interrupting = interaction.act(self._va)
            finally:
                if interrupting is None:
                    if interrupted is not None:
                        self._set_ctx(interrupted.handle_restore(self._va))
                    else:
                        self._set_ctx(self._default_context)
                else:
                    if interrupted is None:
                        self._set_ctx(interrupting)
                    else:
                        self._set_ctx(InterruptContext(interrupted, interrupting))

    def _start_timeout(self):
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
                self._start_timeout()


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
        self._terminated = Event()

    def terminate(self):
        """
        Оповещает поток о необходимости завершить работу.
        """
        self._terminated.set()

    def run(self):
        while True:
            if self._terminated.wait(self._interval):
                logging.debug("Поток отсчёта времени ожидания остановлен")
                return

            # noinspection PyBroadException
            try:
                self._cm.tick_timeout(self._interval)
            except Exception:
                logging.exception("Ошибка при обработке истечения времени ожидания команды")
