from __future__ import annotations

from typing import Any, Dict

from backend.agent.core.tool import BaseTool
from backend.core.models import ToolResult


class FetchTool(BaseTool):
    @property
    def name(self) -> str:
        return "fetch"

    @property
    def description(self) -> str:
        return "Fetch content from a URL"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"url": {"type": "string"}}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult(output={"content": ""})
