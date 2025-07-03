from typing import Any, Optional, Callable

from langchain_core.language_models import BaseChatModel

name = 'llm_ollama'
version = '0.1.0'

config: dict[str, Any] = {
    'model': 'qwen2.5:14b',
    'base_url': None,
    'temperature': 0.8,
}

config_comment = """
Настройки адаптера LLM ollama.

Содержимое этого конфига передаётся в конструктор ChatOllama.
Полный список параметров можно посмотреть в [его документации](https://python.langchain.com/api_reference/ollama/chat_models/langchain_ollama.chat_models.ChatOllama.html).

Ключевые параметры:
- `base_url` - URL сервера ollama
- `model` - название модели
"""


def get_lc_llm(
        nxt: Callable,
        llm: Optional[BaseChatModel],
        llm_settings: dict[str, Any],
        *args, **kwargs
) -> Optional[BaseChatModel]:
    if llm is None and llm_settings['type'] == 'ollama':
        from langchain_ollama import ChatOllama

        settings = llm_settings.copy()
        settings.pop("type")

        llm = ChatOllama(**{**config, **settings})

    return nxt(llm, llm_settings, *args, **kwargs)
