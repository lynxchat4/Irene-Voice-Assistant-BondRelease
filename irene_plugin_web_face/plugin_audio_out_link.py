import uuid
from datetime import datetime, timedelta
from hashlib import md5
from logging import getLogger
from os.path import splitext, normpath
from threading import Event
from typing import Callable, Optional

from fastapi import APIRouter, HTTPException
from starlette.responses import FileResponse

from irene.brain.abc import AudioOutputChannel
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene_plugin_web_face.abc import ProtocolHandler, Connection
from irene_plugin_web_face.protocol import MT_OUT_AUDIO_LINK_PLAYBACK_PROGRESS, MT_OUT_AUDIO_LINK_PLAYBACK_DONE, \
    PROTOCOL_OUT_AUDIO_LINK, MT_OUT_AUDIO_LINK_PLAYBACK_REQUEST


class PlaybackEndSyncer:
    def __init__(self, initial_timeout: float):
        self._evt = Event()
        self._timeout_at: datetime
        self.extend_timeout(initial_timeout)

    def extend_timeout(self, dt):
        self._timeout_at = datetime.utcnow() + timedelta(seconds=dt)

    def playback_finished(self):
        self._evt.set()

    def wait(self):
        while not self._evt.is_set():
            now = datetime.utcnow()
            dt = (self._timeout_at - now).total_seconds()

            if dt <= 0:
                return

            self._evt.wait(dt)


class FileBindings:
    def __init__(self, path_prefix: str):
        self._path_prefix = path_prefix
        self._file_bindings: dict[str, str] = {}

    def add(self, file_path: str) -> str:
        file_path = normpath(file_path)
        name, ext = splitext(file_path)
        bind_name = md5(name.encode()).hexdigest() + ext
        self._file_bindings[bind_name] = file_path

        return bind_name

    def remove(self, bound_name: str):
        # FIXME: если несколько каналов вывода (с отдельными мозгами) попытаются почти одновременно воспроизводить один
        #   файл, то что-нибудь может пойти не так.
        del self._file_bindings[bound_name]

    def get_full_path(self, bound_name: str) -> str:
        return self._path_prefix + '/' + bound_name

    def get_local_path(self, bound_name: str) -> str:
        return self._file_bindings[bound_name]


class WebAudioOutImpl(AudioOutputChannel, ProtocolHandler):
    _logger = getLogger('web-audio-output')

    def __init__(self, conn: Connection, bindings: FileBindings, syncers: dict[str, PlaybackEndSyncer]):
        self._connection = conn
        self._file_bindings = bindings
        self._syncers = syncers

        conn.register_output(self)
        conn.register_message_type(MT_OUT_AUDIO_LINK_PLAYBACK_PROGRESS, self._handle_progress)
        conn.register_message_type(MT_OUT_AUDIO_LINK_PLAYBACK_DONE, self._handle_done)

    def _playback_syncer_for_message(self, msg: dict) -> Optional[PlaybackEndSyncer]:
        playback_id = msg['playbackId']

        try:
            return self._syncers[playback_id]
        except KeyError:
            self._logger.warning(f"Неизвестный идентификатор воспроизведения {playback_id}")
            return None

    def _handle_progress(self, msg: dict):
        if syncer := self._playback_syncer_for_message(msg):
            syncer.extend_timeout(2.0)

    def _handle_done(self, msg: dict):
        if syncer := self._playback_syncer_for_message(msg):
            syncer.playback_finished()

    def start(self):
        pass

    def send_file(self, file_path: str, *, alt_text: Optional[str] = None, **kwargs):
        playback_id = str(uuid.uuid4())
        binding_name = self._file_bindings.add(file_path)
        syncer = PlaybackEndSyncer(2.0)
        try:
            self._syncers[playback_id] = syncer

            message = dict(playbackId=playback_id, url=self._file_bindings.get_full_path(binding_name))

            if alt_text is not None:
                message['altText'] = alt_text

            self._connection.send_message(MT_OUT_AUDIO_LINK_PLAYBACK_REQUEST, message)

            syncer.wait()
        finally:
            del self._syncers[playback_id]
            self._file_bindings.remove(binding_name)

    def terminate(self):
        pass


class WebAudioOutputPlugin(MagicPlugin):
    """
    Отвечает за вывод аудио на клиенте через протокол ``out.audio.link``.
    """
    name = 'web-audio-link-output'
    version = '0.1.0'

    def __init__(self):
        super().__init__()

        self._file_bindings = FileBindings(f'/api/{self.name}/files')
        self._syncers: dict[str, PlaybackEndSyncer] = {}

    def register_fastapi_endpoints(self, router: APIRouter, _pm: PluginManager, *_args, **_kwargs):
        @router.get('/files/{file_name}')
        def get_file(file_name: str):
            try:
                local_path = self._file_bindings.get_local_path(file_name)
            except KeyError:
                raise HTTPException(404)

            return FileResponse(
                local_path,
            )

    def init_client_protocol(
            self,
            nxt: Callable,
            prev: Optional[ProtocolHandler],
            proto_name: str,
            connection: Connection,
            pm: PluginManager,
            *args,
            **kwargs):
        if proto_name == PROTOCOL_OUT_AUDIO_LINK:
            prev = prev or WebAudioOutImpl(connection, self._file_bindings, self._syncers)
        return nxt(prev, proto_name, connection, pm, *args, **kwargs)

    def terminate(self, *_args, **_kwargs):
        for syncer in self._syncers.values():
            syncer.playback_finished()
