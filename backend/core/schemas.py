from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class QueryGenerationOutput(BaseModel):
    reason: str = Field(description="Reasoning process")
    queries: List[str] = Field(min_length=1, max_length=5)
    search_strategy: Literal["broad", "specific", "mixed"]
    metadata: Dict[str, str] = Field(default_factory=dict)
