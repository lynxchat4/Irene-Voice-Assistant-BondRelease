from typing import Optional
from unittest.mock import Mock

from irene.va_abc import VAContext, VAApi


class VAContextMock(VAContext):
    def __init__(self):
        self.timeout_context: Optional[VAContext] = None
        self.cmd_contexts: dict[str, VAContext] = {}
        self.timeout = None

        self.handle_command = Mock(wraps=self.handle_command)
        self.handle_timeout = Mock(wraps=self.handle_timeout)

    def handle_command(self, va: VAApi, text: str) -> Optional[VAContext]:
        return self.cmd_contexts.get(text)

    def handle_timeout(self, va: VAApi) -> Optional[VAContext]:
        return self.timeout_context

    def get_timeout(self, default: float) -> float:
        if self.timeout is None:
            return default
        return self.timeout
