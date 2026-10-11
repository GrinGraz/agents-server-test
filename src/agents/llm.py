"""Fabrica del modelo de lenguaje.

El resto del codigo llama a `get_llm()` y no sabe que proveedor hay detras.
Para cambiar de proveedor basta con la variable de entorno MODEL_PROVIDER.
"""

import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    provider = os.getenv("MODEL_PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5"),
            max_tokens=4096,
        )

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise RuntimeError(
                "Falta langchain-ollama. Ejecuta: uv sync --extra ollama"
            ) from exc

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    raise ValueError(f"MODEL_PROVIDER desconocido: {provider!r} (usa 'anthropic' u 'ollama')")
