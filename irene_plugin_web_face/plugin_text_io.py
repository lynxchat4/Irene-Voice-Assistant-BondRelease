from functools import partial
from typing import Callable, Optional, Any, Mapping

from irene.brain.abc import TextOutputChannel, InboundMessage, OutputChannelPool, VAContext, VAApi
from irene.brain.contexts import BaseContextWrapper
from irene.brain.inbound_messages import PlainTextMessage
from irene.constants.labels import pure_text_channel_labels
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import operation, before, after
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import MT_OUT_TEXT_PLAIN_TEXT, PROTOCOL_OUT_TEXT_PLAIN, MT_IN_TEXT_DIRECT_TEXT, \
    PROTOCOL_IN_TEXT_DIRECT, PROTOCOL_IN_TEXT_INDIRECT, MT_IN_TEXT_INDIRECT_TEXT

name = 'remote_text_protocols'
version = '0.1.0'

config = {
    "output_metadata": pure_text_channel_labels(),
}


class _DirectTextMessage(PlainTextMessage):
    pass


class _TextOutputImpl(TextOutputChannel, ProtocolHandler):
    proto_name = PROTOCOL_OUT_TEXT_PLAIN

    def __init__(self, connection: Connection):
        self._connection = connection
        self._connection.register_output(self)

    def start(self):
        pass

    def send(self, text: str, **kwargs):
        self._connection.send_message(MT_OUT_TEXT_PLAIN_TEXT, {'text': text})

    def terminate(self):
        pass

    @property
    def meta(self) -> Mapping[str, Any]:
        return config['output_metadata']


class _TextInputImpl(ProtocolHandler):
    def __init__(
            self,
            connection: Connection,
            *,
            message_type: str,
            message_class: Callable[[str, OutputChannelPool], InboundMessage],
            proto_name: str,
    ):
        self.proto_name = proto_name
        self._message_class = message_class
        self._connection = connection

        self._connection.register_message_type(message_type, self._handle_client_message)

    def _handle_client_message(self, payload: dict):
        self._connection.receive_inbound_message(
            self._message_class(payload.get('text', ''), self._connection.get_associated_outputs())
        )

    def start(self):
        pass

    def terminate(self):
        pass


_protocols: dict[str, Callable[[Connection], ProtocolHandler]] = {
    PROTOCOL_OUT_TEXT_PLAIN: _TextOutputImpl,
    PROTOCOL_IN_TEXT_DIRECT: partial(
        _TextInputImpl,
        message_type=MT_IN_TEXT_DIRECT_TEXT,
        message_class=_DirectTextMessage,
        proto_name=PROTOCOL_IN_TEXT_DIRECT,
    ),
    PROTOCOL_IN_TEXT_INDIRECT: partial(
        _TextInputImpl,
        message_type=MT_IN_TEXT_INDIRECT_TEXT,
        message_class=PlainTextMessage,
        proto_name=PROTOCOL_IN_TEXT_INDIRECT,
    ),
}


@operation('create_root_context')
@before('add_trigger_phrase')
@after('load_commands')
def skip_trigger_phrase(
        nxt: Callable,
        prev: Optional[VAContext],
        *args, **kwargs,
):
    if prev is None:
        raise ValueError()

    class TriggerPhraseSkipContext(BaseContextWrapper):
        def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
            if isinstance(message.get_original(), _DirectTextMessage):
                return prev.handle_command(va, message)

            return super().handle_command(va, message)

    return TriggerPhraseSkipContext(
        nxt(prev, *args, **kwargs)
    )


def init_client_protocol(
        nxt: Callable,
        prev: Optional[ProtocolHandler],
        proto_name: str,
        connection: Connection,
        pm: PluginManager,
        *args,
        **kwargs):
    if proto_name in _protocols:
        prev = prev or _protocols[proto_name](connection)

    return nxt(prev, proto_name, connection, pm, *args, **kwargs)
