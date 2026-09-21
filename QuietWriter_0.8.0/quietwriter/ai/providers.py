from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass
class StreamChunk:
    content: str = ''
    thinking: str = ''


class AIProvider(ABC):
    """Provider-onafhankelijke AI-interface.

    De rest van QuietWriter kent geen Ollama/OpenRouter details. Nieuwe providers
    hoeven alleen deze kleine interface te implementeren.
    """
    name = 'provider'

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def list_models(self) -> list[dict]: ...

    @abstractmethod
    def stream_chat(self, model: str, messages: list[dict], **options) -> Iterator[StreamChunk]: ...

    def complete(self, model: str, messages: list[dict], **options) -> str:
        parts: list[str] = []
        for chunk in self.stream_chat(model, messages, **options):
            if chunk.content:
                parts.append(chunk.content)
        return ''.join(parts)

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(f'{self.name} ondersteunt in QuietWriter nog geen embeddings.')


class ProviderFactory:
    @staticmethod
    def for_name(settings, provider: str):
        provider = str(provider or 'ollama').lower()
        if provider == 'openrouter':
            from .openrouter_provider import OpenRouterProvider
            return OpenRouterProvider(
                api_key=str(settings.value('openrouter_api_key', '') or ''),
                base_url=str(settings.value('openrouter_url', 'https://openrouter.ai/api/v1') or 'https://openrouter.ai/api/v1'),
            )
        from .ollama_provider import OllamaProvider
        return OllamaProvider(str(settings.value('ollama_url', 'http://127.0.0.1:11434') or 'http://127.0.0.1:11434'))

    @staticmethod
    def from_settings(settings):
        return ProviderFactory.for_name(settings, str(settings.value('ai_provider', 'ollama') or 'ollama'))
