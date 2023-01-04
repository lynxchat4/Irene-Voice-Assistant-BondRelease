from typing import Callable, Optional

from irene.face.abc import MuteGroup, Muteable
from irene.face.mute_group import NULL_MUTE_GROUP
from irene_plugin_web_face.abc import ProtocolHandler, Connection
from irene_plugin_web_face.protocol import PROTOCOL_IN_MUTE, MT_PROTOCOL_IN_MUTE_MUTE, MT_PROTOCOL_IN_MUTE_UNMUTE

name = 'plugin_mute_protocol'
version = '0.1.0'


class _MuteProtocolHandler(ProtocolHandler, Muteable):
    def __init__(self, connection: Connection, mg: MuteGroup):
        self._connection = connection
        self._mg = mg
        self._remove: Optional[Callable] = None

    def start(self):
        self._remove = self._mg.add_item(self)

    def terminate(self):
        if self._remove is not None:
            self._remove()
            self._remove = None

    def mute(self):
        self._connection.send_message(MT_PROTOCOL_IN_MUTE_MUTE, {})

    def unmute(self):
        self._connection.send_message(MT_PROTOCOL_IN_MUTE_UNMUTE, {})


def init_client_protocol(
        nxt: Callable,
        prev: Optional[ProtocolHandler],
        proto_name: str,
        connection: Connection,
        *args,
        **kwargs):
    if proto_name == PROTOCOL_IN_MUTE:
        prev = prev or _MuteProtocolHandler(
            connection,
            kwargs.get('mute_group', NULL_MUTE_GROUP)
        )

    return nxt(prev, proto_name, connection, *args, **kwargs)
