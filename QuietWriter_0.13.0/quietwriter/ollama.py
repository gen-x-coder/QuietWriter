"""Compatibiliteitslaag voor opstart/modeldetectie.

De daadwerkelijke AI-chat zit sinds 0.8.0 in quietwriter.ai. Nieuwe AI-functies
mogen niet rechtstreeks van dit bestand afhankelijk worden.
"""
from __future__ import annotations
from .ai.ollama_provider import OllamaProvider


class OllamaClient:
    def __init__(self, base_url='http://127.0.0.1:11434'):
        self.provider = OllamaProvider(base_url)

    @property
    def base_url(self):
        return self.provider.base_url

    def model_info(self, timeout=2.0) -> list[dict]:
        # timeout blijft voor backwards compatibility; provider hanteert eigen timeout.
        return self.provider.list_models()

    def models(self, timeout=2.0) -> list[str]:
        return [m['name'] for m in self.model_info(timeout)]

    def is_available(self) -> bool:
        return self.provider.is_available()
