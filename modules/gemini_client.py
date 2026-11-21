"""Small wrapper around the Google GenAI SDK."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-4-hydrogen"


def get_model_name() -> str:
    """Return the configured model, or the documented default."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def generate_text(prompt: str, response_schema: dict | None = None) -> str:
    """Send one prompt and return the model's unmodified text response."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is missing. Add your key to the local .env file."
        )

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60_000),
    )
    request_options = {}
    if response_schema is not None:
        request_options["response_format"] = {
            "type": "text",
            "mime_type": "application/json",
            "schema": response_schema,
        }

    response = client.interactions.create(
        model=get_model_name(),
        input=prompt,
        **request_options,
    )
    return response.output_text or ""
