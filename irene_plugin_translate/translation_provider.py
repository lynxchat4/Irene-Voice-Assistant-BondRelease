from abc import abstractmethod, ABC
from typing import Optional


class TranslationProvider(ABC):
    """
    Интерфейс фасада сервиса, осуществляющего перевод текста между разными языками.
    """

    @abstractmethod
    def translate(
            self,
            text: str,
            target_language: str,
            source_language: Optional[str] = None,
            *_args,
            **_kwargs
    ) -> str:
        """
        Переводит строку с одного языка на другой.

        Args:
            text:
                текст, который нужно перевести
            target_language:
                код языка, на который нужно перевести.

                Реализации должны поддерживать как минимум, двух/трёх буквенные коды поддерживаемых языков, согласно
                стандарту BCP-47.
            source_language:
                код языка исходного текста.

                Если ``None`` или пропущен - сервис может попытаться определить язык самостоятельно, однако результат
                такого вызова потенциально непредсказуем.

        Returns:
            переведённый текст.
        """
