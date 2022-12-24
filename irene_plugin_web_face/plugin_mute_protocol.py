from typing import Callable, Optional

from irene.face.abc import MuteGroup, Muteable
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_web_face.abc import ProtocolHandler, Connection
from irene_plugin_web_face.protocol import PROTOCOL_IN_MUTE, MT_PROTOCOL_IN_MUTE_MUTE, MT_PROTOCOL_IN_MUTE_UNMUTE

name = 'plugin_mute_protocol'
version = '0.1.0'


class _MuteProtocolHandler(ProtocolHandler, Muteable):
    def __init__(self, connection: Connection, pm: PluginManager):
        self._connection = connection
        self._pm = pm
        self._remove: Optional[Callable] = None

    def start(self):
        mute_group: Optional[MuteGroup] = call_all_as_wrappers(
            self._pm.get_operation_sequence('get_mute_group'),
            None,
            self._pm,
            connection=self._connection,
        )

        if mute_group is not None:
            self._remove = mute_group.add_item(self)

    def terminate(self):
        if self._remove is not None:
            self._remove()

    def mute(self):
        self._connection.send_message(MT_PROTOCOL_IN_MUTE_MUTE, {})

    def unmute(self):
        self._connection.send_message(MT_PROTOCOL_IN_MUTE_UNMUTE, {})


def init_client_protocol(
        nxt: Callable,
        prev: Optional[ProtocolHandler],
        proto_name: str,
        connection: Connection,
        pm: PluginManager,
        *args,
        **kwargs):
    if proto_name == PROTOCOL_IN_MUTE:
        prev = prev or _MuteProtocolHandler(connection, pm)

    return nxt(prev, proto_name, connection, pm, *args, **kwargs)
