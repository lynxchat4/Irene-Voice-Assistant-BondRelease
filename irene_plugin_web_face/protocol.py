"""
Модуль содержит константы, связанные с базовым протоколом работы ассистента в клиент-серверном режиме, а так же
документацию, описывающую протокол.

Клиент и сервер соединяются по протоколу WebSocket и взаимодействуют обмениваясь текстовыми сообщениями.
Каждое сообщение представляет собой JSON-объект, с одним обязательным полем ``type``, определяющим тип сообщения и
набором дополнительных полей, зависящих от типа сообщения.

Клиент и сервер могут одновременно с основным соединением по WebSocket устанавливать дополнительные соединения в т.ч.
дополнительные WebSocket-соединения.

Связь между клиентом и сервером решает две основные задачи - передачу команд от клиента к серверу и передачу ответов от
сервера к клиенту.
Конкретные способы передачи команд и ответов зависят от используемых соединением протоколов.
Различные клиенты и различные конфигурации сервера могут поддерживать разные наборы протоколов.
Для выбора используемых протоколов при установке соединения осуществляется согласование протоколов.

При подключении клиент отправляет список необходимых ему протоколов в поле ``"protocols"`` сообщения типа
``"negotiate/request"``.
Каждый элемент списка представляет собой список, содержащий названия протоколов, хотя бы один из которых необходим
клиенту для работы.
Сервер выбирает из каждого элемента списка первый поддерживаемый протокол и возвращает список выбранных протоколов в
поле ``"protocols"`` сообщения типа ``"negotiate/agree"``.

Пример:

Клиенту требуется поддержка хотя бы одного из протоколов ``in.text-direct`` и ``in.text-indirect``, а так же хотя бы
одного из протоколов ``out.tts-serverside-file-link`` и ``out.text-plain``.
После подключения клиент отправляет следующее сообщение:

>>> {
>>>     "type": "negotiate/request",
>>>     "protocols": [
>>>         ["in.text-direct", "in.text-indirect"],
>>>         ["out.tts-serverside-file-link", "out.text-plain"]
>>>     ]
>>> }


Допустим, сервер поддерживает протоколы ``in.text-indirect``, ``out.tts-serverside-file-link``, ``out.text-plain``,
тогда он выбирает первый поддерживаемый протокол из каждого элемента списка, полученного от клиента и отвечает следующим
сообщением:

>>> {
>>>     "type": "negotiate/agree",
>>>     "protocols": ["in.text-indirect", "out.tts-serverside-file-link"]
>>> }

Заметьте, что протокол ``out.text-plain`` не возвращается и сервер не обязан поддерживать его в рамках данного
соединения.
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
