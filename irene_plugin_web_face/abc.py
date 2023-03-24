from abc import abstractmethod, ABC
from typing import Callable

from irene.brain.abc import OutputChannel, InboundMessage, OutputChannelPool


class Connection(ABC):
    """
    Интерфейс, через который реализации протоколов клиент-серверного взаимодействия взаимодействуют с отдельно взятым
    клиентским соединением.
    """

    __slots__ = ()

    @abstractmethod
    def register_message_type(self, mt: str, handler: Callable[[dict], None]):
        """
        Регистрирует обработчик сообщения, полученного от клиента.

        Args:
            mt:
                тип сообщения
            handler:
                обработчик сообщения.
        """

    @abstractmethod
    def send_message(self, mt: str, payload: dict):
        """
        Отправляет сообщение клиенту.

        Args:
            mt:
                тип сообщения
            payload:
                тело сообщения
        """

    @abstractmethod
    def register_output(self, ch: OutputChannel):
        """
        Регистрирует канал вывода, связанный с этим соединением.

        Args:
            ch:
                канал вывода
        """

    @abstractmethod
    def get_associated_outputs(self) -> OutputChannelPool:
        """
        Возвращает пул каналов вывода, связанных с этим соединением.

        Returns:
            пул каналов вывода, связанных с этим соединением
        """

    @abstractmethod
    def receive_inbound_message(self, im: InboundMessage):
        """
        Оповещает ассистента о получении входящего сообщения от клиента.

        Args:
            im:
                входящее сообщение
        """


class ProtocolHandler(ABC):
    """
    Сущность, отвечающая за обработку одного протокола взаимодействия с клиентом для одного соединения.

    Создаётся в процессе согласования протоколов.
    Конструктор, как правило, принимает объект соединения (``Connection``) и регистрирует обработчики входящих сообщений
    (``register_message_type``) и каналы вывода (``register_output``).
    """

    __slots__ = ()

    proto_name: str

    @abstractmethod
    def start(self):
        """
        Вызывается когда все протоколы для соединения уже согласованы.

        Может выделять тяжёлые ресурсы, требующие явного освобождения.
        """

    @abstractmethod
    def terminate(self):
        """
        Вызывается при завершении соединения.

        Вызывается только если ``start`` был ранее успешно вызван.
        """
