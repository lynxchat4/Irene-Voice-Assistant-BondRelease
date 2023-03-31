import unittest

from irene import VAApiExt, ContextTimeoutException
from irene.brain.contexts import construct_context
from irene.test_utuls import DialogTestCase


def _hi(va: VAApiExt, _text: str):
    va.say("привет")


class FunctionalContextsTest(DialogTestCase):
    def _timer(self, va: VAApiExt, text: str):
        if text.startswith("на "):
            self._timer_set(va, text)
            return

        va.say("на сколько?")

        if text == "не спеша":
            va.context_set(self._timer_set, 30)
        elif text.startswith("чтобы "):
            va.context_set((self._timer_set_with_purpose, text[6:]))
        else:
            va.context_set(self._timer_set)

    @staticmethod
    def _timer_set(va: VAApiExt, text: str):
        va.say(f"ставлю таймер на {text[3:]}")

    @staticmethod
    def _timer_set_with_purpose(va: VAApiExt, text: str, purpose: str):
        va.say(f"ставлю таймер на {text[3:]} чтобы {purpose}")

    def setUp(self):
        self.using_context({
            "привет": _hi,
            "поставь таймер": self._timer
        })

    def test_str_simple_fn(self):
        ctx = construct_context(self._timer)

        self.assertRegex(
            str(ctx),
            r'test_functional_contexts\.FunctionalContextsTest\._timer'
        )

    def test_str_with_args(self):
        ctx = construct_context(
            (self._timer_set_with_purpose, "сварить пельмени"))

        self.assertRegex(
            str(ctx),
            r'test_functional_contexts\.FunctionalContextsTest\._timer_set_with_purpose.*сварить пельмени'
        )

    def test_simple_function(self):
        self.play_scenario("""
        > поставь таймер на пять минут
        < ставлю таймер на пять минут

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_context_change(self):
        self.play_scenario("""
        > поставь таймер
        < на сколько\\?
        > на пол часа
        < ставлю таймер на пол часа
        
        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout(self):
        self.play_scenario("""
        > поставь таймер
        < на сколько\\?
        ! wait 20
        
        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout_override(self):
        self.play_scenario("""
        > поставь таймер не спеша
        < на сколько\\?
        ! wait 20
        > на пол часа
        < ставлю таймер на пол часа

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_additional_argument(self):
        self.play_scenario("""
        > поставь таймер чтобы сварить пельмени
        < на сколько\\?
        > на семь минут
        < ставлю таймер на семь минут чтобы сварить пельмени

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)


class GeneratorContextTest(DialogTestCase):
    @staticmethod
    def _timer_gen(_va: VAApiExt, text: str):
        duration = None

        try:
            if text.startswith("на "):
                duration = text[3:]
            else:
                text = yield "на сколько?"

                while duration is None:
                    if text.startswith("на "):
                        duration = text[3:]
                    else:
                        text = yield "не поняла"
        except ContextTimeoutException:
            return "ладно, не буду ставить таймер"

        return f"ставлю таймер на {duration}"

    @staticmethod
    def _timer_gen_slow(va: VAApiExt, text: str):
        duration = None

        try:
            if text.startswith("на "):
                duration = text[3:]
            else:
                text = yield "на сколько? не торопись с ответом", 30

                while duration is None:
                    if text.startswith("на "):
                        duration = text[3:]
                    else:
                        text = yield "не поняла"
        except ContextTimeoutException:
            va.say("ладно, не буду ставить таймер")

        return f"ставлю таймер на {duration}"

    @staticmethod
    def _timer_gen_annoying(_va: VAApiExt, _text: str):
        duration = None

        question = "на сколько?"

        while duration is None:
            try:
                text = yield question
            except ContextTimeoutException:
                question = "отвечай уже, насколько ставить таймер?"
                continue

            if text.startswith("на "):
                duration = text[3:]
            else:
                question = "не поняла"

        return f"ставлю таймер на {duration}"

    @staticmethod
    def _timer_gen_careless(_va: VAApiExt, text: str):
        duration = None

        if text.startswith("на "):
            duration = text[3:]
        else:
            text = yield "на сколько?"

            while duration is None:
                if text.startswith("на "):
                    duration = text[3:]
                else:
                    text = yield "не поняла"

        return f"ставлю таймер на {duration}"

    @staticmethod
    def _offensive_behavior(va: VAApiExt, _text: str):
        yield f"""пф, "{va.get_message().get_original().get_text()}", тоже мне интеллигент"""
        return f"""сам {va.get_message().get_original().get_text()}"""

    def setUp(self):
        self.using_context({
            "привет": _hi,
            "категорически": self._offensive_behavior,
            "поставь таймер": self._timer_gen,
            "поставь таймер не спеша": self._timer_gen_slow,
            "поставь таймер наверняка": self._timer_gen_annoying,
            "поставь таймер или забей": self._timer_gen_careless,
        })

    def test_no_yields(self):
        self.play_scenario("""
        > поставь таймер на пять минут
        < ставлю таймер на пять минут

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_one_yield(self):
        self.play_scenario("""
        > поставь таймер
        < на сколько\\?
        > на пять минут
        < ставлю таймер на пять минут

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_loop(self):
        self.play_scenario("""
        > поставь таймер
        < на сколько\\?
        > мяу
        < не поняла
        > я кот, я не понимаю, чего ты от меня хочешь
        < не поняла
        > ладно, на пять минут
        < не поняла
        > на пять минут
        < ставлю таймер на пять минут

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout(self):
        self.play_scenario("""
        > поставь таймер
        < на сколько\\?
        ! wait 20
        < ладно, не буду ставить таймер

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout_override(self):
        self.play_scenario("""
        > поставь таймер не спеша
        < на сколько\\? не торопись с ответом
        ! wait 20
        > на пять минут
        < ставлю таймер на пять минут

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout_override_next_calls(self):
        self.play_scenario("""
        > поставь таймер не спеша
        < на сколько\\? не торопись с ответом
        ! wait 20
        > мяу
        < не поняла
        ! wait 20
        > я кот, я не понимаю, чего ты от меня хочешь
        < не поняла
        ! wait 20
        > ладно, на пять минут
        < не поняла
        ! wait 20
        > на пять минут
        < ставлю таймер на пять минут

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout_restart(self):
        self.play_scenario("""
        > поставь таймер наверняка
        < на сколько\\?
        ! wait 11
        < отвечай уже, насколько ставить таймер\\?
        ! wait 11
        < отвечай уже, насколько ставить таймер\\?
        > пять минут
        < не поняла
        > на стол
        < ставлю таймер на стол

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_timeout_not_intercepted(self):
        self.play_scenario("""
        > поставь таймер или забей
        < на сколько\\?
        ! wait 20
        <

        # убеждаемся, что диалог вернулся к изначальному контексту
        > привет
        < привет
        """)

    def test_access_original_message(self):
        self.play_scenario("""
        > Категорически приветствую!
        < пф, "категорически приветствую", тоже мне интеллигент
        > дура
        < сам дура
        """)


if __name__ == '__main__':
    unittest.main()
