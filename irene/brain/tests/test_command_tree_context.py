import unittest
from typing import Optional
from unittest.mock import Mock

from irene import VAApi, VAContext
from irene.brain.abc import InboundMessage
from irene.brain.contexts import construct_context, CommandTreeContext
from irene.test_utuls import VAContextMock
from irene.test_utuls.stub_text_message import tm


class CommandTreeContextTest(unittest.TestCase):
    def setUp(self):
        self.va = Mock(spec=VAApi)
        self.c1 = VAContextMock()
        self.c2 = VAContextMock()
        self.c3 = VAContextMock()

    def test_construct(self):
        self.assertIsInstance(
            construct_context({}),
            CommandTreeContext
        )

    def test_construct_overrides(self):
        class _LoopCtx(VAContext):
            def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
                return self

        ctx = construct_context(
            {
                "включи свет": self.c1,
                "выключи свет": self.c1,
            },
            unknown_command_context=_LoopCtx,
            ambiguous_command_context=_LoopCtx
        )

        unknown_ctx = ctx.handle_command(self.va, tm("привет"))
        ambiguous_ctx = ctx.handle_command(self.va, tm("включи выключи свет"))

        self.assertIsInstance(unknown_ctx, _LoopCtx)
        self.assertIsInstance(ambiguous_ctx, _LoopCtx)
        self.assertIs(unknown_ctx, ambiguous_ctx)

    def test_find_command(self):
        self.c1.cmd_contexts[''] = self.c2

        ctx = construct_context({
            "привет": self.c1
        })

        self.assertIs(
            ctx.handle_command(self.va, tm("привет")),
            self.c2
        )

    def test_unknown_default(self):
        self.c1.cmd_contexts["привет"] = self.c2
        ctx = construct_context({}, ambiguous_command_context=self.c1)

        self.assertIs(
            ctx.handle_command(self.va, tm("привет")),
            ctx
        )

    def test_ambiguous_default(self):
        ctx = construct_context({
            "включи свет": self.c1,
            "выключи свет": self.c1,
        })

        self.assertIs(
            ctx.handle_command(self.va, tm("включи выключи свет")),
            ctx
        )

    def test_ambiguous_from_unknown(self):
        self.c1.cmd_contexts["включи выключи свет"] = self.c2
        ctx = construct_context({
            "включи свет": self.c1,
            "выключи свет": self.c1,
        }, unknown_command_context=self.c1)

        self.assertIs(
            ctx.handle_command(self.va, tm("включи выключи свет")),
            self.c2
        )

    def test_unknown_override(self):
        self.c1.cmd_contexts["привет"] = self.c2
        ctx = construct_context({}, unknown_command_context=self.c1)

        self.assertIs(
            ctx.handle_command(self.va, tm("привет")),
            self.c2
        )

    def test_ambiguous_override(self):
        self.c1.cmd_contexts["включи выключи свет"] = self.c2
        ctx = construct_context({
            "включи свет": self.c1,
            "выключи свет": self.c1,
        }, ambiguous_command_context=self.c1)

        self.assertIs(
            ctx.handle_command(self.va, tm("включи выключи свет")),
            self.c2
        )


if __name__ == '__main__':
    unittest.main()
