from typing import Any, Callable, Optional

from langchain_core.language_models import BaseChatModel

name = "llm_openai"
version = "0.1.0"

config: dict[str, Any] = {
    "url": None,
    "model": "gpt-4o-mini",
}

config_comment = """
Настройки адаптера LLM OpenAI.

Содержимое этого конфига передаётся в конструктор ChatOpenAI.
Полный список параметров можно посмотреть в [его документации](https://python.langchain.com/api_reference/openai/chat_models/langchain_openai.chat_models.base.ChatOpenAI.html).

Ключевые параметры:
- `base_url` - URL сервера OpenAI.
            Если установлен `null`, то будет использоваться непосредственно API компании OpenAI.
            Указав другой URL, можно использовать прокси или другой совместимый сервис.
- `model` - название модели

При использовании моделей от OpenAI не следует передавать лишние или неподдерживаемые параметры.
В частности, некоторые модели (`o*`) не поддерживают параметр `temperature` и не работают, если его указать.
"""


def get_lc_llm(
        nxt: Callable,
        llm: Optional[BaseChatModel],
        llm_settings: dict[str, Any],
        *args, **kwargs
) -> Optional[BaseChatModel]:
    if llm is None and llm_settings['type'] == 'openai':
        from langchain_openai import ChatOpenAI

        settings = llm_settings.copy()
        settings.pop("type")

        llm = ChatOpenAI(**{**config, **settings})

    return nxt(llm, llm_settings, *args, **kwargs)
