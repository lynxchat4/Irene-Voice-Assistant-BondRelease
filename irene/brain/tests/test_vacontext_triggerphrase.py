import unittest
from unittest.mock import Mock

from irene.brain.abc import VAApi
from irene.brain.contexts import TriggerPhraseContext
from irene.test_utuls import VAContextMock
from irene.test_utuls.stub_text_message import tm


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
            c.handle_command(self.va, tm("ирина привет")),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, tm("ирина пока")),
            self.ctx2
        )

    def test_simple_phrase_omit_prefix(self):
        c = TriggerPhraseContext([["ирина"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, tm("бла бла бла ирина привет")),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, tm("привет ирина пока")),
            self.ctx2
        )

    def test_simple_phrase_no_match(self):
        c = TriggerPhraseContext([["ирина"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, tm("ира привет")),
            None
        )
        self.next_ctx.handle_command.assert_not_called()

    def test_long_phrase(self):
        c = TriggerPhraseContext(
            [["окей", "ирина", "ивановна"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, tm("окей ирина ивановна привет")),
            self.ctx1
        )

    def test_varying_phrase(self):
        c = TriggerPhraseContext(
            [["ирина"], ["ирины"], ["ирину"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, tm("ирина привет")),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, tm("ирины привет")),
            self.ctx1
        )
        self.assertIs(
            c.handle_command(self.va, tm("ирину привет")),
            self.ctx1
        )

    def test_forward_direct_message(self):
        c = TriggerPhraseContext(
            [["ирина"], ["ирины"], ["ирину"]], self.next_ctx)
        self.assertIs(
            c.handle_command(self.va, tm("привет", {'is_direct': True})),
            self.ctx1
        )


if __name__ == '__main__':
    unittest.main()
