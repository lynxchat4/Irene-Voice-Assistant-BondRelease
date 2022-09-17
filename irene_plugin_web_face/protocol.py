"""
Модуль содержит константы, связанные с базовым протоколом работы ассистента в клиент-серверном режиме.
"""

MESSAGE_TYPE_KEY = 'type'

MT_NEGOTIATE_REQUEST = 'negotiate/request'
MT_NEGOTIATE_AGREE = 'negotiate/agree'

PROTOCOL_IN_TEXT_INDIRECT = 'in.text-indirect'
MT_IN_TEXT_INDIRECT_TEXT = f'{PROTOCOL_IN_TEXT_INDIRECT}/text'

PROTOCOL_IN_TEXT_DIRECT = 'in.text-direct'
MT_IN_TEXT_DIRECT_TEXT = f'{PROTOCOL_IN_TEXT_DIRECT}/text'

PROTOCOL_OUT_TEXT_PLAIN = 'out.text-plain'
MT_OUT_TEXT_PLAIN_TEXT = f'{PROTOCOL_OUT_TEXT_PLAIN}/text'

PROTOCOL_OUT_AUDIO_LINK = 'out.audio.link'
MT_OUT_AUDIO_LINK_PLAYBACK_REQUEST = f'{PROTOCOL_OUT_AUDIO_LINK}/playback-request'
MT_OUT_AUDIO_LINK_PLAYBACK_PROGRESS = f'{PROTOCOL_OUT_AUDIO_LINK}/playback-progress'
MT_OUT_AUDIO_LINK_PLAYBACK_DONE = f'{PROTOCOL_OUT_AUDIO_LINK}/playback-done'

PROTOCOL_OUT_SERVER_SIDE_TTS = 'out.tts.serverside'
