from logging import getLogger
from typing import Optional, Callable, TypedDict

from irene.brain.abc import OutputChannelPool, Brain
from irene.brain.inbound_messages import PlainTextMessage
from irene.brain.output_pool import OutputPoolImpl
from irene.face.abc import LocalInput, MuteGroup
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, after
from irene.plugin_loader.run_operation import call_all_as_wrappers


class LocalSpeechFacePlugin(MagicPlugin):
    """
    Обеспечивает работу ассистента с аудио (и прочим) вводом-выводом через устройства на локальной машине.
    """

    name = 'face_local'
    version = '0.2.1'

    _logger = getLogger(name)

    config_comment = """
    Настройки ввода-вывода через локальные устройства.
    
    Доступны следующие параметры:
    
    - `input`     - Метод ввода команд.
                    Объект, обычно содержащий, как минимум поле `type` определяющее используемый метод ввода.
                    Так же, может содержать дополнительные параметры, зависящие от конкретного метода.
    - `outputs`   - Методы вывода ответов ассистента.
                    Содержит список объектов, каждый из которых соответствует одному из методов вывода.
                    Аналогично методу ввода, объекты, как правило, содержат поле `type` и иногда набор дополнительных
                    специфических полей.
                    Подробная информация по настройке методов ввода и вывода доступна по следующей ссылке:
                    https://github.com/AlexeyBond/Irene-Voice-Assistant/blob/master/doc/local-face.md
    - `muteGroup` - См. [ДОКУМЕНТ НЕ СОЗДАН]
    """

    class _Config(TypedDict):
        input: dict
        outputs: list[dict]
        muteGroup: dict

    config: _Config = {
        'input': {
            'type': 'vosk+sounddevice',
        },
        'outputs': [
            {
                'type': 'sounddevice',
            },
            {
                'type': 'tts',
                'profile_selector': {},
            },
        ],
        'muteGroup': {},
    }

    def __init__(self) -> None:
        super().__init__()
        self._brain: Optional[Brain] = None
        self._input: Optional[LocalInput] = None
        self._outputs: Optional[OutputChannelPool] = None
        self._stop: Optional[Callable[[], None]] = None

    def receive_config(self, config: _Config, *_args, **_kwargs):
        for output_conf in config['outputs']:
            # В версии 0.6.0 тип канала вывода, используемый по-умолчанию (tts-file) был удалён.
            if output_conf.get('type') == 'tts-file':
                self._logger.info("Обновляю устаревшую конфигурацию канала вывода (tts-file -> tts)")
                output_conf.clear()
                output_conf['type'] = 'tts'
                output_conf['profile_selector'] = {}

    @after('create_brain')
    def init(self, pm: PluginManager, *_args, **_kwargs):
        self._brain = call_all_as_wrappers(
            pm.get_operation_sequence('get_brain'),
            None,
            pm
        )

        if self._brain is None:
            self._logger.error("Не удалось найти мозг")
            return

        mute_group: Optional[MuteGroup] = call_all_as_wrappers(
            pm.get_operation_sequence('get_mute_group'),
            None,
            pm,
            self.config['muteGroup'],
        )

        if mute_group is None:
            mute_group = NULL_MUTE_GROUP

        self._input = call_all_as_wrappers(
            pm.get_operation_sequence('create_local_input'),
            None,
            pm,
            self.config['input'],
            mute_group=mute_group,
        )

        if self._input is None:
            self._logger.error(
                "Не удалось найти или инициализировать выбранный метод ввода команд"
            )
            return

        output_configs = self.config['outputs']

        if len(output_configs) == 0:
            self._logger.error("Не настроен ни один канал вывода")

        outputs = []

        for output_config in output_configs:
            new_outputs = call_all_as_wrappers(
                pm.get_operation_sequence('create_local_outputs'),
                [],
                pm,
                output_config,
                mute_group=mute_group,
            )

            if len(new_outputs) == 0:
                self._logger.error(
                    "Не удалось создать канал вывода из настроек %s",
                    output_config
                )
                continue

            outputs.extend(new_outputs)

        if len(outputs) == 0:
            self._logger.error(
                "Не удалось инициализировать ни один из каналов вывода"
            )
            return

        self._outputs = OutputPoolImpl(outputs)

    def run(self, *_args, **_kwargs):
        if self._brain is None or self._input is None or self._outputs is None:
            return

        with self._brain.send_messages(self._outputs) as send_message:
            with self._input.run() as (commands, stop):
                self._stop = stop

                for command in commands:
                    send_message(PlainTextMessage(command, self._outputs))

    def terminate(self, *_args, **_kwargs):
        if self._stop:
            self._stop()
