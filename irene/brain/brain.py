from contextlib import contextmanager
from typing import Optional, Any

from irene.brain.abc import VAContext, OutputChannelPool, VAApi, VAActiveInteractionSource, InboundMessage, Brain, \
    VAContextConstructor
from irene.brain.active_interaction import construct_active_interaction
from irene.brain.context_manager import VAContextManager, TimeoutTicker
from irene.brain.output_pool import CompositeOutputPool, EMPTY_OUTPUT_POOL


class _VAApiProvider:
    __slots__ = ('_outputs', '_context_manager', '_construct_context')

    def __init__(
            self,
            *,
            outputs: OutputChannelPool,
            context_constructor: VAContextConstructor,
    ):
        self._outputs = outputs
        self._context_manager: Optional[VAContextManager] = None
        self._construct_context = context_constructor

    def use_context_manager(self, cm: VAContextManager):
        """
        Между ``VAContextManager``ом и реализацией ``VAApi`` есть циклическая зависимость, из-за которой ссылку
        на экземпляр ``VAContextManager`` приходится инициализировать отложено.
        Для этого и используется этот метод.

        Args:
            cm:
        """
        self._context_manager = cm

    def get_api(self) -> VAApi:
        """
        Возвращает готовый к использованию экземпляр ``VAApi``.
        """
        provider = self

        class VAApiImpl(VAApi):
            # Экземпляр создаётся таким образом - с передачей зависимостей через замыкание и запретом на добавление
            # новых полей чтобы не давать плагинам доступа к тому, к чему доступа у них быть не должно, в т.ч. не давать
            # создавать новые поля т.к. в некоторых случаях это может не работать. Это сделано для предотвращения
            # возможных проблем с совместимостью в будущем.
            __slots__ = ()

            def get_outputs(self) -> OutputChannelPool:
                return provider._outputs

            def submit_active_interaction(
                    self,
                    interaction: VAActiveInteractionSource,
                    *,
                    related_message: Optional[InboundMessage] = None,
            ):
                if provider._context_manager is None:
                    raise RuntimeError('submit_active_interaction вызван до инициализации ссылки на VAContextManager')

                ai = construct_active_interaction(
                    interaction,
                    related_message=related_message,
                    construct_context=provider._construct_context,
                )
                provider._context_manager.process_active_interaction(ai)

        return VAApiImpl()


class BrainImpl(Brain):
    def __init__(
            self,
            *,
            main_context: VAContext,
            config: dict[str, Any],
            predefined_outputs: OutputChannelPool = EMPTY_OUTPUT_POOL,
            context_constructor: VAContextConstructor,
    ):
        self._config = config
        self._outputs = CompositeOutputPool((predefined_outputs,))
        self._api_provider = _VAApiProvider(outputs=self._outputs, context_constructor=context_constructor)

        self._context_manager = VAContextManager(
            self._api_provider.get_api(),
            main_context,
            config.get('defaultTimeout', 10.0),
        )

        self._ticker: Optional[TimeoutTicker] = None

        if not config.get('timeoutsDisabled', False):
            self._ticker = TimeoutTicker(self._context_manager, config.get('timeoutCheckInterval', 1.0))
            self._ticker.start()

    def _process_message(self, message: InboundMessage):
        self._context_manager.process_command(message)

    @contextmanager
    def send_messages(self, outputs: OutputChannelPool):
        self._outputs.insert(0, outputs)

        try:
            yield self._process_message
        finally:
            self._outputs.remove(outputs)

    def kill(self):
        if self._ticker:
            self._ticker.terminate()
            self._ticker.join()
            self._ticker = None
