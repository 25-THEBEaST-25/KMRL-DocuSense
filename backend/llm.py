"""
LLM wrapper. Uses the OpenAI Python SDK, but points at whatever
OpenAI-compatible base_url you set in .env — so it works unmodified
with OpenAI, Groq (free), or a local Ollama server.
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.getenv("LLM_API_KEY", ""),
)
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_ENABLED = bool(os.getenv("LLM_API_KEY", "").strip()) and os.getenv("LLM_API_KEY", "").strip() != "your_groq_key_here"


def chat(system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.2) -> str:
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        **kwargs,
    )
    return response.choices[0].message.content


def chat_json(system_prompt: str, user_prompt: str) -> dict:
    """Calls the LLM and safely parses a JSON response."""
    raw = chat(system_prompt, user_prompt, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # strip markdown fences if the model added them anyway
        cleaned = raw.strip().strip("```json").strip("```").strip()
        return json.loads(cleaned)
