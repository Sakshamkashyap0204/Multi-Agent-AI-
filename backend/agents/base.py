import os
import json
from typing import Optional
from openai import AsyncOpenAI

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> Optional[AsyncOpenAI]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your-openai-api-key-here":
        return None
    if _client is None:
        try:
            _client = AsyncOpenAI(api_key=api_key)
        except Exception:
            return None
    return _client


async def call_llm(system_prompt: str, user_message: str, model: str = None, response_format: dict = None) -> Optional[str]:
    client = get_openai_client()
    if not client:
        return None

    try:
        kwargs = {
            "model": model or DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print("[WARN] LLM call failed, falling back to simulated output:", e)
        return None


def parse_json_response(text: str) -> dict:
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
    return {}
