import unittest
from unittest.mock import Mock

from test_utuls import VAContextMock
from vaabstract import VAApi
from vacontextmanager import VAContextManager


class VAContextManagerTest(unittest.TestCase):
    def setUp(self):
        self.hi_to_ctx = VAContextMock()

        self.hi_ctx = VAContextMock()
        self.hi_ctx.timeout_context = self.hi_to_ctx

        self.default_ctx = VAContextMock()

        self.default_ctx.cmd_contexts["привет"] = self.hi_ctx

        self.va = Mock(spec=VAApi)
        self.mgr = VAContextManager(self.va, self.default_ctx)

    def test_invoke_default_context(self):
        self.mgr.process_command("привет")
        self.default_ctx.handle_command.assert_called_once_with(self.va, "привет")

    def test_switch_from_default_context(self):
        self.mgr.process_command("привет")
        self.mgr.process_command("пока")

        self.hi_ctx.handle_command.assert_called_once_with(self.va, "пока")

    def test_no_timeout_before_start(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command("привет")

        self.mgr.tick_timeout(1000.0)

        self.hi_ctx.handle_timeout.assert_not_called()

    def test_no_timeout_before_time_comes(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command("привет")
        self.mgr.start_timeout()

        self.mgr.tick_timeout(0.9)

        self.hi_ctx.handle_timeout.assert_not_called()

    def test_timeout(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command("привет")
        self.mgr.start_timeout()

        self.mgr.tick_timeout(1.001)

        self.hi_ctx.handle_timeout.assert_called_once_with(self.va)

    def test_timeout_context_switch(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command("привет")
        self.mgr.start_timeout()

        self.mgr.tick_timeout(1.001)

        self.mgr.process_command("пока")

        self.hi_to_ctx.handle_command.assert_called_once_with(self.va, "пока")


if __name__ == '__main__':
    unittest.main()
