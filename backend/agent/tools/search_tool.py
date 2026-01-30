from __future__ import annotations

from typing import Any, Dict

from backend.agent.core.tool import BaseTool
from backend.core.models import ToolResult


class SearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search the web using a provider"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"query": {"type": "string"}}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult(output={"results": []})
