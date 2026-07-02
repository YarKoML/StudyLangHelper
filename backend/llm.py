"""Клиент к OpenAI-совместимому LLM-провайдеру (BYOK)."""

import httpx

from backend.models import LLMSettings

REQUEST_TIMEOUT = 30


def derive_models_url(base_url: str) -> str:
    """base_url указывает на /v1/chat/completions → вернуть /v1/models."""
    url = base_url.rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")]
    return f"{url}/models"


def list_provider_models(base_url: str, api_key: str) -> list[str]:
    models_url = derive_models_url(base_url)
    try:
        r = httpx.get(
            models_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMProviderError(f"Failed to fetch models: {e}") from e

    try:
        data = r.json()
    except ValueError as e:
        raise LLMProviderError(f"Invalid JSON from provider: {e}") from e

    models: list[str] = []
    if isinstance(data, dict) and "data" in data:
        for item in data["data"]:
            if isinstance(item, dict) and "id" in item:
                models.append(str(item["id"]))
    return sorted(models)


def translate_text(text: str, target_lang_name: str, settings: LLMSettings) -> str:
    system_prompt = (
        f"You are a translator. Translate the user's text into {target_lang_name}. "
        "Return only the translation, nothing else."
    )
    try:
        r = httpx.post(
            settings.base_url,
            headers={"Authorization": f"Bearer {settings.api_key}"},
            json={
                "model": settings.model,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
            },
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise LLMProviderError(f"Translation request failed: {e}") from e

    try:
        data = r.json()
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, ValueError) as e:
        raise LLMProviderError(f"Unexpected provider response: {e}") from e


class LLMProviderError(Exception):
    """Ошибка при обращении к LLM-провайдеру."""
