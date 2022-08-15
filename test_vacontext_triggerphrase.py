import unittest
from unittest.mock import Mock

from test_utuls import VAContextMock
from vaabstract import VAApi
from vacontext import TriggerPhraseContext


class TriggerPhraseContextTest(unittest.TestCase):
    def setUp(self):
        self.ctx1 = VAContextMock()
        self.ctx2 = VAContextMock()

        self.next_ctx = VAContextMock()
        self.next_ctx.cmd_contexts["привет"] = self.ctx1
        self.next_ctx.cmd_contexts["пока"] = self.ctx2

        self.va = Mock(spec=VAApi)

    def test_simple_phrase(self):
        c = TriggerPhraseContext([["ирина"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, "ирина привет"),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, "ирина пока"),
            self.ctx2
        )

    def test_simple_phrase_omit_prefix(self):
        c = TriggerPhraseContext([["ирина"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, "бла бла бла ирина привет"),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, "привет ирина пока"),
            self.ctx2
        )

    def test_simple_phrase_no_match(self):
        c = TriggerPhraseContext([["ирина"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, "ира привет"),
            None
        )
        self.next_ctx.handle_command.assert_not_called()

    def test_long_phrase(self):
        c = TriggerPhraseContext([["окей", "ирина", "ивановна"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, "окей ирина ивановна привет"),
            self.ctx1
        )

    def test_varying_phrase(self):
        c = TriggerPhraseContext([["ирина"], ["ирины"], ["ирину"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, "ирина привет"),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, "ирины привет"),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, "ирину привет"),
            self.ctx1
        )


if __name__ == '__main__':
    unittest.main()
