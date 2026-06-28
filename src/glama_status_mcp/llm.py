"""LLM provider with fleet Glom-On auto-discovery.

Detects Ollama (11434), LM Studio (1234) automatically.
Supports OpenAI-compatible APIs via env vars.
"""

import os
from dataclasses import dataclass, field

import httpx

_DEFAULT_MODELS: dict[str, str] = {
    "ollama": "llama3.2:3b",
    "lmstudio": "auto",
    "openai": "gpt-4o-mini",
}

_LOCAL_PORTS: dict[str, int] = {
    "ollama": 11434,
    "lmstudio": 1234,
}


@dataclass
class Provider:
    name: str
    base_url: str
    available: bool = False
    models: list[str] = field(default_factory=list)


async def _probe_port(port: int, timeout: float = 2.0) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.get(f"http://127.0.0.1:{port}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def discover_providers() -> list[Provider]:
    providers: list[Provider] = []

    # Ollama
    ollama = Provider(
        name="ollama",
        base_url=f"http://127.0.0.1:{_LOCAL_PORTS['ollama']}/v1",
    )
    if await _probe_port(_LOCAL_PORTS["ollama"]):
        ollama.available = True
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(
                    f"http://127.0.0.1:{_LOCAL_PORTS['ollama']}/api/tags"
                )
                models = r.json().get("models", [])
                ollama.models = [m["name"] for m in models[:20]]
        except Exception:  # noqa: S110
            pass
    providers.append(ollama)

    # LM Studio
    lmstudio = Provider(
        name="lmstudio",
        base_url=f"http://127.0.0.1:{_LOCAL_PORTS['lmstudio']}/v1",
    )
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get(
                f"http://127.0.0.1:{_LOCAL_PORTS['lmstudio']}/v1/models"
            )
            if r.status_code == 200:
                lmstudio.available = True
                data = r.json().get("data", [])
                lmstudio.models = [m["id"] for m in data[:20]]
    except Exception:  # noqa: S110
        pass
    providers.append(lmstudio)

    # OpenAI (via env var)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai = Provider(
        name="openai",
        base_url=openai_base,
        available=bool(openai_key),
    )
    if openai.available:
        openai.models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    providers.append(openai)

    return providers


async def chat(
    provider: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    api_key: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(url, json=payload, headers=headers)
        if r.status_code != 200:
            raise RuntimeError(
                f"LLM error {r.status_code}: {r.text[:500]}"
            )
        data = r.json()
        return data["choices"][0]["message"]["content"]
