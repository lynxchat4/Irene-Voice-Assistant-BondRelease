import unittest
from typing import Optional, Type

from irene import VAApiExt, ContextTimeoutException, VAContext, VAApi
from irene.active_interaction import construct_active_interaction
from irene.test_utuls import DialogTestCase
from irene.va_abc import InboundMessage, VAActiveInteraction


class ActiveInteractionConstructorTest(unittest.TestCase):
    def stub_interaction_fn(self, va):
        pass

    def test_function(self):
        self.assertIsInstance(
            construct_active_interaction(self.stub_interaction_fn),
            VAActiveInteraction
        )

    def test_ready_made_object(self):
        obj = construct_active_interaction(self.stub_interaction_fn)

        self.assertIs(construct_active_interaction(obj), obj)

    def test_class(self):
        class _TestInteraction(VAActiveInteraction):
            def act(self, va: VAApi) -> Optional[VAContext]:
                pass

        self.assertIsInstance(
            construct_active_interaction(_TestInteraction),
            _TestInteraction
        )

    def test_illegal_source(self):
        with self.assertRaises(Exception):
            # Значение неверного типа передано намеренно
            # noinspection PyTypeChecker
            construct_active_interaction('foo')


class ActiveInteractionTest(DialogTestCase):
    @staticmethod
    def timer_interaction(va: VAApiExt):
        va.play_audio('media/timer.wav')
        va.say("время вышло")

    def message_interaction(self, va: VAApiExt):
        va.play_audio('media/message.wav')

        try:
            self.assertEqual(
                (yield "у тебя новое сообщение"),
                "прочитай"
            )
            self.assertEqual(
                (yield "типа текст сообщения"),
                "это спам"
            )
            return "сообщение отмечено как спам"
        except ContextTimeoutException:
            return "ладно, фиг с ним с сообщением"

    def noop_ctx(self, va, text):
        pass

    def make_bla_bla_bla_context(self) -> VAContext:
        test = self

        class BlaBlaContext(VAContext):
            def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
                test.assertRegex(
                    message.get_text(),
                    r'(бла ?)+'
                )

                va.say(message.get_text() + " бла")

                return self

            def handle_interrupt(self, va: VAApi):
                va.say("появилось кое-что более важное, чем бла бла бла")
                return self

            def handle_restore(self, va: VAApi):
                va.say("вернёмся к бла бла бла")
                return self

        return BlaBlaContext()

    def make_unimportant_context(self) -> Type[VAContext]:
        test = self

        class UnimportantContext(VAContext):
            def handle_command(self, va: VAApi, message: InboundMessage) -> Optional['VAContext']:
                test.assertRegex(
                    message.get_text(),
                    r'(бла ?)+'
                )

                va.say(message.get_text() + " бла")

                return self

            def handle_interrupt(self, va: VAApi) -> Optional[VAContext]:
                va.say("хватит бла бла бла на сегодня")
                return None

            def handle_restore(self, va: VAApi) -> Optional[VAContext]:
                raise AssertionError('UnimportantContext никогда не должен восстанавливаться')

        return UnimportantContext

    def test_simple_interaction(self):
        self.using_context(self.noop_ctx)

        self.play_scenario(f"""
        ! act timer_interaction
        < {self.expect_playback('media/timer.wav')} время вышло
        """)

    def test_complex_interaction(self):
        self.using_context(self.noop_ctx)

        self.play_scenario(f"""
        ! act message_interaction
        < {self.expect_playback('media/message.wav')} у тебя новое сообщение
        > прочитай
        < типа текст сообщения
        > это спам
        < сообщение отмечено как спам
        """)

    def test_interaction_timeout(self):
        self.using_context(self.noop_ctx)
        self.va.submit_active_interaction(self.message_interaction)

        self.play_scenario(f"""
        < {self.expect_playback('media/message.wav')} у тебя новое сообщение
        ! wait 20.0
        < ладно, фиг с ним с сообщением
        """)

    def test_interaction_timeout1(self):
        self.using_context(self.noop_ctx)
        self.va.submit_active_interaction(self.message_interaction)

        self.play_scenario(f"""
        < {self.expect_playback('media/message.wav')} у тебя новое сообщение
        > прочитай
        < типа текст сообщения
        ! wait 20.0
        < ладно, фиг с ним с сообщением
        """)

    def test_interrupt_and_restore_context(self):
        self.using_context(self.make_bla_bla_bla_context())
        self.play_scenario(f"""
        > бла бла бла
        < бла бла бла бла
        ! act message_interaction
        < появилось кое-что более важное, чем бла бла бла {self.expect_playback('media/message.wav')} у тебя новое сообщение
        > прочитай
        < типа текст сообщения
        > это спам
        < сообщение отмечено как спам вернёмся к бла бла бла
        > бла
        < бла бла
        """)

    def test_interrupt_and_restore_context_deep(self):
        self.using_context(self.make_bla_bla_bla_context())
        self.play_scenario(f"""
        > бла бла бла
        < бла бла бла бла
        ! act message_interaction
        < появилось кое-что более важное, чем бла бла бла {self.expect_playback('media/message.wav')} у тебя новое сообщение
        > прочитай
        < типа текст сообщения
        ! act timer_interaction
        < {self.expect_playback('media/timer.wav')} время вышло
        > это спам
        < сообщение отмечено как спам вернёмся к бла бла бла
        > бла
        < бла бла
        """)

    def test_interrupt_and_restore_with_simple_interaction(self):
        self.using_context(self.make_bla_bla_bla_context())
        self.play_scenario(f"""
        > бла бла бла
        < бла бла бла бла
        ! act timer_interaction
        < появилось кое-что более важное, чем бла бла бла {self.expect_playback('media/timer.wav')} время вышло вернёмся к бла бла бла
        > бла
        < бла бла
        """)

    def test_interrupt_unimportant_context_with_simple_interaction(self):
        self.using_context(self.make_unimportant_context())
        self.play_scenario(f"""
        > бла бла бла
        < бла бла бла бла
        ! act timer_interaction
        < хватит бла бла бла на сегодня {self.expect_playback('media/timer.wav')} время вышло
        # диалог возвращается к контексту по-умолчанию, восстановления контекста не происходит
        > бла
        < бла бла
        """)

    def test_interrupt_unimportant_context_with_complex_interaction(self):
        self.using_context(self.make_unimportant_context())
        self.play_scenario(f"""
        > бла бла бла
        < бла бла бла бла
        ! act message_interaction
        < хватит бла бла бла на сегодня {self.expect_playback('media/message.wav')} у тебя новое сообщение
        > прочитай
        < типа текст сообщения
        > это спам
        < сообщение отмечено как спам
        # диалог возвращается к контексту по-умолчанию, восстановления контекста не происходит
        > бла
        < бла бла
        """)

    @staticmethod
    def _faulty_interaction(va: VAApiExt):
        # метод get_original_message работоспособен только в обработчиках контекста, в активном взаимодействии он
        # выкидывает ошибку, т.к. в общем случае оно не является реакцией на какое-либо сообщение
        va.get_message()

    def test_get_original_message_call_error(self):
        self.using_context(self.noop_ctx)

        with self.assertRaises(RuntimeError):
            self.va.submit_active_interaction(self._faulty_interaction)

    @staticmethod
    def _timeout_override_context(_va: VAApiExt, _text: str):
        try:
            answer = yield "у тебя 30 секунд чтобы ответить на мой вопрос", 30
        except ContextTimeoutException:
            return "слишком долго"

        return f"и {answer} - это правильный ответ"

    def test_interaction_during_timeout_override(self):
        self.using_context(self._timeout_override_context)
        self.play_scenario(f"""
        > привет
        < у тебя 30 секунд чтобы ответить на мой вопрос
        ! wait 29
        ! act timer_interaction
        # не то время (!)
        < {self.expect_playback('media/timer.wav')} время вышло
        ! wait 29
        > 42
        < и 42 - это правильный ответ
        """)

    def test_interaction_during_timeout_override_exceed_timeout_after(self):
        self.using_context(self._timeout_override_context)
        self.play_scenario(f"""
        > привет
        < у тебя 30 секунд чтобы ответить на мой вопрос
        ! wait 29
        ! act timer_interaction
        # не то время (!)
        < {self.expect_playback('media/timer.wav')} время вышло
        ! wait 30.1
        < слишком долго
        """)


if __name__ == '__main__':
    unittest.main()
