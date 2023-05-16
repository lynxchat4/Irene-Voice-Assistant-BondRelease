import asyncio
import datetime
import json
import pathlib
import uuid
from argparse import ArgumentParser
from asyncio import AbstractEventLoop
from logging import getLogger
from threading import Lock
from typing import Callable, Optional, Any

import vosk  # type: ignore
from fastapi import APIRouter, Query, HTTPException
from starlette.websockets import WebSocket, WebSocketDisconnect

from irene.brain.abc import InboundMessage, VAContext, VAApi
from irene.brain.contexts import BaseContextWrapper
from irene.brain.inbound_messages import PlainTextMessage
from irene.face.abc import MuteGroup, Muteable
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.file_patterns import first_substitution
from irene.plugin_loader.magic_plugin import operation, after, before, step_name
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import MT_IN_SERVER_SIDE_STT_RECOGNIZED, MT_IN_SERVER_SIDE_STT_PROCESSED, \
    MT_IN_SERVER_SIDE_STT_READY, PROTOCOL_IN_SERVER_SIDE_STT, IN_SERVER_SIDE_STT_DEFAULT_SAMPLE_RATE

name = 'plugin_in_stt_serverside'
version = '0.1.0'

_logger = getLogger(name)


class _ServerSttMessage(PlainTextMessage):
    __slots__ = ('_connection', '_processed')

    def __init__(self, connection: Connection, text: str):
        super().__init__(text, connection.get_associated_outputs())

        self._connection = connection
        self._processed = False

    def notify_processed(self, text: str):
        if not self._processed:
            self._processed = True
            self._connection.send_message(
                MT_IN_SERVER_SIDE_STT_PROCESSED,
                dict(text=text)
            )


class _InterceptionContext(BaseContextWrapper):
    def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
        if isinstance(orig := message.get_original(), _ServerSttMessage):
            orig.notify_processed(message.get_text())

        return super().handle_command(va, message)


_dump_path_template: Optional[str] = None


def setup_cli_arguments(ap: ArgumentParser, *_args, **_kwargs):
    ap.add_argument(
        '--dump-server-stt-input',
        metavar='<шаблон пути>',
        help="Сохраняет полученные через веб-интерфейс аудио-данные в файл.",
        type=str,
        dest='serverside_stt_dump_path_template',
        default=None,
    )


def receive_cli_arguments(args: Any, *_args, **_kwargs):
    global _dump_path_template

    if (path_template := args.serverside_stt_dump_path_template) is None:
        return

    try:
        first_substitution(path_template, override_vars=dict(
            connection_id='test', timestamp='42'))
    except Exception:
        _logger.exception(
            "Шаблон, переданный через параметр --dump-server-stt-input не корректен и будет проигнорирован")
    else:
        _dump_path_template = path_template


@operation('create_root_context')
@after('load_commands')
@before('add_trigger_phrase')
@step_name('intercept_server_stt_messages')
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


class _RecognizerStopException(Exception):
    pass


class _RecognizerWorker(Muteable):
    """
    Поток, отвечающий за распознание речи для отдельного соединения.
    """

    def __init__(
            self,
            connection: Connection,
            mute_group: MuteGroup,
            model,
            sample_rate: int,
            connection_id: str,
    ):
        self._connection = connection
        self._buffer: list[bytes] = []
        self._buffer_length: int = 0
        self._recognizer = vosk.KaldiRecognizer(model, sample_rate)
        self._need_stop = False

        self._mute_group = mute_group
        self._muted = False

        self._connection_id = connection_id
        self._dump_file = None

        self._event_loop: Optional[AbstractEventLoop] = None
        self._mx = Lock()

    def mute(self):
        self._muted = True
        self._event_loop.call_soon_threadsafe(
            self._event_loop.run_in_executor,
            None, self._cmd_reset_recognizer
        )

    def unmute(self):
        self._muted = False

    def stop(self):
        self._need_stop = True

    def _cmd_reset_recognizer(self) -> None:
        with self._mx:
            self._recognizer.Reset()

    def _cmd_process_data_chunk(self, chunk) -> None:
        if self._muted:
            return

        if self._dump_file:
            self._dump_file.write(chunk)
            self._dump_file.flush()

        with self._mx:
            if not self._recognizer.AcceptWaveform(chunk):
                return

            recognized = json.loads(self._recognizer.Result())
            text = recognized['text']

        if len(text) > 0 and not self._muted:
            _logger.debug("Распознано: %s", text)

            self._connection.send_message(
                MT_IN_SERVER_SIDE_STT_RECOGNIZED, dict(text=text))

            self._connection.receive_inbound_message(
                _ServerSttMessage(self._connection, text)
            )

    def _cmd_stop(self) -> None:
        raise _RecognizerStopException()

    def _open_dump_file(self):
        if (tpl := _dump_path_template) is None:
            return

        timestamp = str(int(datetime.datetime.utcnow().timestamp()))
        path = first_substitution(
            tpl,
            override_vars=dict(
                connection_id=self._connection_id, timestamp=timestamp)
        )

        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

        self._dump_file = open(path, 'wb')

    def _close_dump_file(self):
        if (file := self._dump_file) is None:
            return

        self._dump_file = None
        file.close()

    async def process_connection(self, ws: WebSocket):
        self._event_loop = asyncio.get_running_loop()

        remove_from_mute_group = self._mute_group.add_item(self)

        await self._event_loop.run_in_executor(
            None,
            self._open_dump_file
        )

        try:
            while not self._need_stop:
                chunk = await ws.receive_bytes()

                await self._event_loop.run_in_executor(
                    None,
                    self._cmd_process_data_chunk,
                    chunk
                )
        except WebSocketDisconnect:
            _logger.info("Соединение с клиентом разорвано")
        finally:
            try:
                self.stop()
            finally:
                remove_from_mute_group()

            await self._event_loop.run_in_executor(
                None,
                self._close_dump_file
            )


class _ServerSTTHandler(ProtocolHandler):
    def __init__(self, connection: Connection, mute_group: MuteGroup, model, path: str, handler_id: str):
        self._id = handler_id
        self._connection = connection
        self._mute_group = mute_group
        self._model = model
        self._path = path
        self._workers: list[_RecognizerWorker] = []

    def start(self):
        self._connection.send_message(
            MT_IN_SERVER_SIDE_STT_READY,
            dict(path=self._path)
        )

        _handlers[self._id] = self

    async def accept_connection(self, ws: WebSocket, sample_rate: int):
        await ws.accept()

        worker = _RecognizerWorker(
            self._connection, self._mute_group, self._model, sample_rate, self._id)
        self._workers.append(worker)

        try:
            await worker.process_connection(ws)
        finally:
            self._workers.remove(worker)

    def terminate(self):
        for worker in self._workers[:]:
            worker.stop()

        del _handlers[self._id]


_handlers: dict[str, _ServerSTTHandler] = {}


def init_client_protocol(
        nxt: Callable,
        prev: Optional[ProtocolHandler],
        proto_name: str,
        connection: Connection,
        pm: PluginManager,
        *args,
        **kwargs):
    if proto_name == PROTOCOL_IN_SERVER_SIDE_STT:
        model = call_all_as_wrappers(
            pm.get_operation_sequence('get_vosk_model'),
            None,
        )

        if model is None:
            _logger.warning("Не удалось получить модель для vosk")
        else:
            handler_id = str(uuid.uuid4())

            prev = prev or _ServerSTTHandler(
                connection,
                kwargs.get('mute_group', NULL_MUTE_GROUP),
                model,
                f'/api/{name}/{handler_id}',
                handler_id,
            )

    return nxt(prev, proto_name, connection, pm, *args, **kwargs)


def register_fastapi_endpoints(router: APIRouter, *_args, **_kwargs):
    @router.websocket('/{handler_id}')
    async def serve_ws(
            ws: WebSocket,
            handler_id: str,
            sample_rate: int = Query(
                default=IN_SERVER_SIDE_STT_DEFAULT_SAMPLE_RATE),
    ):
        try:
            handler = _handlers[handler_id]
        except KeyError:
            raise HTTPException(404)

        await handler.accept_connection(ws, sample_rate)
