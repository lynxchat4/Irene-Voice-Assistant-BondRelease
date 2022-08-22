from typing import Optional
from unittest.mock import Mock

from irene.brain.abc import VAContext, VAApi, InboundMessage


class VAContextMock(VAContext):
    def __init__(self):
        self.timeout_context: Optional[VAContext] = None
        self.cmd_contexts: dict[str, VAContext] = {}
        self.timeout = None

        self.handle_command_text = Mock(wraps=self.handle_command_text)
        self.handle_command = Mock(wraps=self.handle_command)
        self.handle_timeout = Mock(wraps=self.handle_timeout)

    def handle_command_text(self, va: VAApi, text: str):
        """
        Mock-метод, которому от сообщения передаётся только текст.
        Для более удобного сопоставления текста с ожидаемым.
        """
        ...

    def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
        self.handle_command_text(va, message.get_text())
        return self.cmd_contexts.get(message.get_text())

    def handle_timeout(self, va: VAApi) -> Optional[VAContext]:
        return self.timeout_context

    def get_timeout(self, default: float) -> float:
        if self.timeout is None:
            return default
        return self.timeout
