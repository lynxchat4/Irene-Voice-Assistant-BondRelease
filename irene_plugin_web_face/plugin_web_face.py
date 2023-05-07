import asyncio
from logging import getLogger
from typing import Callable, Collection, Optional, Any

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from irene.brain.abc import Brain, OutputChannel, InboundMessage, OutputChannelPool
from irene.brain.output_pool import OutputPoolImpl
from irene.face.abc import MuteGroup
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import MESSAGE_TYPE_KEY, MT_NEGOTIATE_REQUEST, MT_NEGOTIATE_AGREE


class _ConnectionImpl(Connection):
    __slots__ = (
        '_websocket', '_message_handlers', '_event_loop', '_outputs_pool', '_message_processor', '_protocols'
    )

    _logger = getLogger('ws-api')

    def __init__(self, ws: WebSocket):
        self._websocket = ws
        self._message_handlers: dict[str, Callable[[dict], None]] = {}
        self._event_loop = asyncio.get_running_loop()
        self._outputs_pool = OutputPoolImpl(())
        self._message_processor: Optional[Callable[[
            InboundMessage], None]] = None
        self._protocols: list[ProtocolHandler] = []

    def register_output(self, ch: OutputChannel):
        self._outputs_pool.append(ch)

    def get_associated_outputs(self) -> OutputChannelPool:
        return self._outputs_pool

    def _process_inbound_message(self, im: InboundMessage):
        if (mp := self._message_processor) is None:
            raise Exception()

        mp(im)

    def receive_inbound_message(self, im: InboundMessage):
        self._event_loop.run_in_executor(None, self._process_inbound_message, im)

    def register_message_type(self, mt: str, handler: Callable[[dict], None]):
        if mt in self._message_handlers:
            raise ValueError(
                f"Назначено более одного обработчика для сообщения типа '{mt}'")

        self._message_handlers[mt] = handler

    def send_message(self, mt: str, payload: dict):
        self._event_loop.call_soon_threadsafe(
            self._event_loop.create_task,
            self._websocket.send_json({**payload, 'type': mt}),
        )

    async def on_message_received(self, msg: dict):
        try:
            mt = msg[MESSAGE_TYPE_KEY]
        except KeyError:
            self._logger.warning("Получено некорректное сообщение")
            return

        try:
            handler = self._message_handlers[mt]
        except KeyError:
            self._logger.warning(
                f"Получено сообщение неизвестного типа: '{mt}'")
            return

        self._event_loop.run_in_executor(None, handler, msg)

    def negotiate_protocols(self, pm: PluginManager, msg: Any):
        if msg.get('type', None) != MT_NEGOTIATE_REQUEST:
            raise ValueError(
                "Получено неожиданное сообщение в процессе согласования протоколов"
            )

        protocols: Collection[str] = msg['protocols']

        if len(protocols) == 0:
            raise ValueError("Клиент не передал список необходимых протоколов")

        negotiated = []
        proto_handlers: list[ProtocolHandler] = []

        mute_group: MuteGroup = call_all_as_wrappers(
            pm.get_operation_sequence('get_mute_group'),
            None,
            pm,
            {},
            connection=self,
        ) or NULL_MUTE_GROUP

        def _negotiate_variants(protocol_variants: str):
            for variant in protocol_variants:
                if variant is None or variant in negotiated:
                    negotiated.append(variant)
                    return

                proto = call_all_as_wrappers(
                    pm.get_operation_sequence('init_client_protocol'),
                    None,
                    variant,
                    self,
                    pm,
                    mute_group=mute_group,
                )

                if proto is None:
                    continue

                if not isinstance(proto, ProtocolHandler):
                    raise ValueError(
                        f"Объект типа {type(proto)} получен при попытке инициализировать протокол "
                        f"'{variant}' вместо экземпляра {ProtocolHandler}"
                    )

                proto_handlers.append(proto)

                negotiated.append(variant)
                return

            raise _UnsupportedProtocolsException(protocol_variants)

        for variants in protocols:
            _negotiate_variants(variants)

        self.send_message(MT_NEGOTIATE_AGREE, {'protocols': negotiated})

        for handler in proto_handlers:
            handler.start()
            self._protocols.append(handler)

    def set_message_processor(self, im_handler: Callable[[InboundMessage], None]):
        self._message_processor = im_handler

    def terminate(self):
        self._outputs_pool.clear()

        for proto in self._protocols:
            proto.terminate()

    @property
    def client_address(self):
        return getattr(self._websocket.client, 'host', '[АДРЕС НЕИЗВЕСТЕН]')


class _UnsupportedProtocolsException(Exception):
    def __init__(self, variants: str):
        super().__init__(
            f"Ни один из следующих протоколов не поддерживается: {variants}")


class WebFacePlugin(MagicPlugin):
    name = 'face_web'
    version = '0.0.1'

    _logger = getLogger('face_web')

    def __init__(self):
        super().__init__()

        self._active_connections: set[_ConnectionImpl] = set()

    def register_fastapi_endpoints(self, router: APIRouter, pm: PluginManager, *_args, **_kwargs):
        brain: Brain = call_all_as_wrappers(
            pm.get_operation_sequence('get_brain'), None, pm)

        if brain is None:
            raise Exception("Не удалось найти мозг.")

        @router.websocket('/ws')
        async def process_socket(ws: WebSocket):
            connection = _ConnectionImpl(ws)
            event_loop = asyncio.get_running_loop()

            await ws.accept()

            try:
                await event_loop.run_in_executor(
                    None,
                    connection.negotiate_protocols,
                    pm, await ws.receive_json(),
                )
            except Exception as e:
                self._logger.exception(
                    f"Отказ клиенту %s в подключении",
                    connection.client_address,
                )
                await ws.close(reason=str(e))
                await event_loop.run_in_executor(None, connection.terminate)
                return

            with brain.send_messages(connection.get_associated_outputs()) as send_message:
                try:
                    connection.set_message_processor(send_message)
                    self._active_connections.add(connection)

                    while True:
                        im = await ws.receive_json()
                        await connection.on_message_received(im)
                except WebSocketDisconnect:
                    self._logger.info(
                        f"Соединение с клиентом {connection.client_address} разорвано")
                except Exception as e:
                    self._logger.exception(
                        f"Ошибка при обработке сообщений от удалённого клиента")
                    await ws.close(4500, reason=str(e))
                finally:
                    self._active_connections.remove(connection)
                    await event_loop.run_in_executor(None, connection.terminate)

    def terminate(self, *_args, **_kwargs):
        for connection in self._active_connections:
            # noinspection PyBroadException
            try:
                connection.terminate()
            except Exception:
                self._logger.exception(
                    f"Ошибка при закрытии соединения с клиентом {connection.client_address}"
                )
