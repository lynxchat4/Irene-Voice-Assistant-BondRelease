from functools import partial
from typing import Callable, Optional, TypedDict, Any

from irene.brain.abc import TextOutputChannel
from irene.brain.inbound_messages import PlainTextMessage
from irene.constants.labels import pure_text_channel_labels
from irene.plugin_loader.abc import PluginManager
from irene.utils.metadata import MetadataMapping
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import MT_OUT_TEXT_PLAIN_TEXT, PROTOCOL_OUT_TEXT_PLAIN, MT_IN_TEXT_DIRECT_TEXT, \
    PROTOCOL_IN_TEXT_DIRECT, PROTOCOL_IN_TEXT_INDIRECT, MT_IN_TEXT_INDIRECT_TEXT

name = 'remote_text_protocols'
version = '0.2.0'


class _Config(TypedDict):
    output_metadata: dict[str, Any]


config: _Config = {
    "output_metadata": pure_text_channel_labels(),
}


class _TextOutputImpl(TextOutputChannel, ProtocolHandler):
    __slots__ = '_connection'
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
    def meta(self) -> MetadataMapping:
        return config['output_metadata']


class _TextInputImpl(ProtocolHandler):
    __slots__ = ('proto_name', '_message_meta', '_connection')

    def __init__(
            self,
            connection: Connection,
            *,
            message_type: str,
            message_meta: Optional[MetadataMapping],
            proto_name: str,
    ):
        self.proto_name = proto_name
        self._message_meta = message_meta
        self._connection = connection

        self._connection.register_message_type(message_type, self._handle_client_message)

    def _handle_client_message(self, payload: dict):
        self._connection.receive_inbound_message(
            PlainTextMessage(
                payload.get('text', ''),
                self._connection.get_associated_outputs(),
                self._message_meta,
            )
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
        message_meta={'is_direct': True},
        proto_name=PROTOCOL_IN_TEXT_DIRECT,
    ),
    PROTOCOL_IN_TEXT_INDIRECT: partial(
        _TextInputImpl,
        message_type=MT_IN_TEXT_INDIRECT_TEXT,
        message_meta=None,
        proto_name=PROTOCOL_IN_TEXT_INDIRECT,
    ),
}


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
