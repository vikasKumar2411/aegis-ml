import json
import os
from typing import Any, Dict, Optional

import requests


class LLMClient:
    """
    Provider-agnostic LLM client.

    Phase 2 starts with local Ollama support so AegisML can run without
    paid API keys. Later we can add OpenAI / Bedrock behind the same interface.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.provider = provider or os.getenv("AEGIS_LLM_PROVIDER", "ollama")
        self.model = model or os.getenv("AEGIS_LLM_MODEL", "qwen2.5:7b-instruct")
        self.timeout_seconds = timeout_seconds
        self.ollama_url = os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434",
        )

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate structured JSON.

        If the LLM fails, returns the deterministic fallback with warning metadata.
        """
        if self.provider == "ollama":
            return self._generate_json_ollama(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                fallback=fallback,
            )

        fallback["_llm_warning"] = f"Unsupported LLM provider: {self.provider}"
        return fallback

    def _generate_json_ollama(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = f"""
{system_prompt}

Return ONLY valid JSON. Do not include markdown, commentary, or explanation.

User input:
{user_prompt}
""".strip()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
            },
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            raw = response.json().get("response", "")
            parsed = json.loads(raw)

            parsed["_llm_provider"] = self.provider
            parsed["_llm_model"] = self.model

            return parsed

        except Exception as exc:
            fallback["_llm_warning"] = f"Ollama generation failed: {exc}"
            fallback["_llm_provider"] = self.provider
            fallback["_llm_model"] = self.model
            fallback["_used_fallback"] = True
            return fallback