from time import sleep

import utils.num_to_text_ru as num_to_text
from irene import VAApiExt
from irene.plugin_loader.magic_plugin import MagicPlugin, after

female_units_min2 = ((u'минуту', u'минуты', u'минут'), 'f')
female_units_min = ((u'минута', u'минуты', u'минут'), 'f')
female_units_sec2 = ((u'секунду', u'секунды', u'секунд'), 'f')
female_units_sec = ((u'секунда', u'секунды', u'секунд'), 'f')


class TimerPlugin(MagicPlugin):
    name = 'plugin_timer'
    version = '7.0.0'

    config = {
        'wavRepeatTimes': 2,
        'wavPath': 'media/timer.wav',
    }

    @after('config')
    def start(self, pm, *_args, **_kwargs):
        ...  # TODO: start timer thread

    def terminate(self, pm, *_args, **_kwargs):
        ...  # TODO: stop timer thread

    def define_commands(self, *_args, **_kwargs):
        return {
            "поставь таймер|поставь тайгер|таймер|тайгер": self._set_timer
        }

    def _set_timer_real(self, va: VAApiExt, time: int, text: str) -> str:
        def done_interaction(va: VAApiExt):
            for i in range(self.config['wavRepeatTimes']):
                va.play_audio(self.config['wavPath'])
                sleep(0.2)

            va.say(f"{text} прошло")

        def submit_interaction():
            va.submit_active_interaction(done_interaction)

        # TODO: Schedule submit_interaction() call

        return f"поставила таймер на {text}"

    def _set_timer(self, va: VAApiExt, phrase: str):
        if phrase == "":
            # таймер по умолчанию - на 5 минут
            self._set_timer_real(va, 5 * 60, "пять минут")
            return

        phrase += " "

        if phrase.startswith("на "):  # вырезаем "на " (из фразы "на Х минут")
            phrase = phrase[3:]

        # ставим секунды?
        for i in range(100, 1, -1):
            txt = num_to_text.num2text(i, female_units_sec) + " "
            if phrase.startswith(txt):
                # print(txt)
                self._set_timer_real(va, i, txt)
                return

            txt2 = num_to_text.num2text(i, female_units_sec2) + " "
            if phrase.startswith(txt2):
                # print(txt,txt2)
                self._set_timer_real(va, i, txt)
                return

            txt3 = str(i) + " секунд "
            if phrase.startswith(txt3):
                # print(txt,txt2)
                self._set_timer_real(va, i, txt)
                return

        # ставим минуты?
        for i in range(100, 1, -1):
            txt = num_to_text.num2text(i, female_units_min) + " "
            if phrase.startswith(txt):
                self._set_timer_real(va, i * 60, txt)
                return

            txt2 = num_to_text.num2text(i, female_units_min2) + " "
            if phrase.startswith(txt2):
                self._set_timer_real(va, i * 60, txt)
                return

            txt3 = str(i) + " минут "
            if phrase.startswith(txt3):
                # print(txt,txt2)
                self._set_timer_real(va, i * 60, txt)
                return

        # без указания единиц измерения - ставим минуты
        for i in range(100, 1,
                       -1):  # обратный вариант - иначе "двадцать" находится быстрее чем "двадцать пять", а это неверно
            txt = num_to_text.num2text(i, female_units_min) + " "
            txt2 = num_to_text.num2text(i) + " "
            if phrase.startswith(txt2):
                self._set_timer_real(va, i * 60, txt)
                return

            txt3 = str(i) + " "
            if phrase.startswith(txt3):
                self._set_timer_real(va, i * 60, txt)
                return

        # спецкейс под одну минуту
        if phrase.startswith("один ") or phrase.startswith("одна ") or phrase.startswith("одну "):
            txt = num_to_text.num2text(1, female_units_min)
            self._set_timer_real(va, 1 * 60, txt)
            return

        # непонятно, но сохраняем контекст и переспрашиваем время
        va.say("Что после таймер?")
        va.context_set(self._set_timer)
