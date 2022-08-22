import time
import unittest
from unittest.mock import Mock, call, patch

from irene.brain.abc import VAApi
from irene.brain.context_manager import VAContextManager, TimeoutTicker
from irene.test_utuls import VAContextMock
from irene.test_utuls.stub_text_message import tm


class ContextManagerTest(unittest.TestCase):
    def setUp(self):
        self.hi_to_ctx = VAContextMock()

        self.hi_ctx = VAContextMock()
        self.hi_ctx.timeout_context = self.hi_to_ctx

        self.default_ctx = VAContextMock()

        self.default_ctx.cmd_contexts["привет"] = self.hi_ctx

        self.va = Mock(spec=VAApi)
        self.mgr = VAContextManager(self.va, self.default_ctx)

    def test_invoke_default_context(self):
        self.mgr.process_command(tm("привет"))
        self.default_ctx.handle_command_text.assert_called_once_with(self.va, "привет")

    def test_switch_from_default_context(self):
        self.mgr.process_command(tm("привет"))
        self.mgr.process_command(tm("пока"))

        self.hi_ctx.handle_command_text.assert_called_once_with(self.va, "пока")

    def test_no_timeout_before_time_comes(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command(tm("привет"))

        self.mgr.tick_timeout(0.9)

        self.hi_ctx.handle_timeout.assert_not_called()

    def test_timeout(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command(tm("привет"))

        self.mgr.tick_timeout(1.001)

        self.hi_ctx.handle_timeout.assert_called_once_with(self.va)

    def test_timeout_context_switch(self):
        self.hi_ctx.timeout = 1.0
        self.mgr.process_command(tm("привет"))

        self.mgr.tick_timeout(1.001)

        self.mgr.process_command(tm("пока"))

        self.hi_to_ctx.handle_command_text.assert_called_once_with(self.va, "пока")


class TimeoutTickerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cm = Mock(spec=VAContextManager)

    def test_terminate(self):
        ticker = TimeoutTicker(self.cm)
        ticker.start()

        ticker.terminate()

        # Зависнет если остановка потока не сработает
        ticker.join()

    def test_call_context_manager(self):
        ticker = TimeoutTicker(self.cm, 0.1)
        ticker.start()
        time.sleep(0.5)
        ticker.terminate()

        self.assertIn(
            self.cm.tick_timeout.call_count,
            range(4, 6)
        )
        for c in self.cm.tick_timeout.call_args_list:
            self.assertEqual(
                c,
                call(0.1)
            )

    @patch('logging.exception')
    def test_error_handling(self, exception_logger_mock):
        # TimeoutTicker должен продолжать дёргать cm.tick_timeout даже если тот бросает исключения
        self.cm.tick_timeout.side_effect = Exception('test!')

        ticker = TimeoutTicker(self.cm, 0.1)
        ticker.start()
        time.sleep(0.5)
        ticker.terminate()

        self.assertIn(
            self.cm.tick_timeout.call_count,
            range(4, 6)
        )
        for c in self.cm.tick_timeout.call_args_list:
            self.assertEqual(
                c,
                call(0.1)
            )
        exception_logger_mock.assert_called()


if __name__ == '__main__':
    unittest.main()
