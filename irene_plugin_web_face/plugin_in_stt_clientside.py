from typing import Callable, Optional

from irene.brain.abc import OutputChannelPool, VAContext, VAApi, InboundMessage
from irene.brain.contexts import BaseContextWrapper
from irene.brain.inbound_messages import PlainTextMessage
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import operation, after, before, step_name
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import MT_IN_CLIENT_SIDE_STT_PROCESSED, PROTOCOL_IN_CLIENT_SIDE_STT, \
    MT_IN_CLIENT_SIDE_STT_RECOGNIZED

name = 'plugin_in_stt_clientside'
version = '0.1.0'


class _ClientSTTMessage(PlainTextMessage):
    __slots__ = ('_connection', '_processed')

    def __init__(self, text: str, outputs: OutputChannelPool, connection: Connection):
        super().__init__(text, outputs)
        self._connection = connection
        self._processed = False

    def notify_processed(self, text: str):
        if not self._processed:
            self._processed = True
            self._connection.send_message(
                MT_IN_CLIENT_SIDE_STT_PROCESSED,
                dict(text=text),
            )


class _InterceptionContext(BaseContextWrapper):
    def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
        if isinstance(orig := message.get_original(), _ClientSTTMessage):
            orig.notify_processed(message.get_text())

        return super().handle_command(va, message)


@operation('create_root_context')
@after('load_commands')
@before('add_trigger_phrase')
@step_name('intercept_client_stt_messages')
def intercept_processed_stt_messages_on_root(
        nxt: Callable,
        prev: VAContext,
        *args, **kwargs,
):
    return nxt(
        _InterceptionContext(prev),
        *args, **kwargs,
    )


@operation('construct_context')
@after('construct_default')
def intercept_processed_stt_messages_everywhere(
        nxt: Callable,
        prev: VAContext,
        *args, **kwargs
):
    return nxt(
        _InterceptionContext(prev),
        *args, **kwargs,
    )


class _ClientsideSTTProtocolHandler(ProtocolHandler):
    def __init__(self, connection: Connection):
        self._connection = connection

        connection.register_message_type(
            MT_IN_CLIENT_SIDE_STT_RECOGNIZED,
            self._handle_recognized_message,
        )

    def _handle_recognized_message(self, msg: dict):
        self._connection.receive_inbound_message(
            _ClientSTTMessage(msg['text'], self._connection.get_associated_outputs(), self._connection)
        )

    def start(self):
        pass

    def terminate(self):
        pass


def init_client_protocol(
        nxt: Callable,
        prev: Optional[ProtocolHandler],
        proto_name: str,
        connection: Connection,
        pm: PluginManager,
        *args,
        **kwargs):
    if proto_name == PROTOCOL_IN_CLIENT_SIDE_STT:
        prev = prev or _ClientsideSTTProtocolHandler(connection)

    return nxt(prev, proto_name, connection, pm, *args, **kwargs)
