from typing import Type

from pydantic import BaseModel

from backend.utils.exceptions import LLMResponseParseError


def parse_llm_response(response: str, model: Type[BaseModel]) -> BaseModel:
    clean = response.strip()
    if clean.startswith("```"):
        clean = clean.split("```", 2)[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.strip()
    try:
        return model.model_validate_json(clean)
    except Exception as exc:  # noqa: BLE001
        raise LLMResponseParseError(f"Invalid response format: {exc}") from exc
