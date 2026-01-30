from __future__ import annotations

from typing import Any, Dict

from backend.agent.core.tool import BaseTool
from backend.core.models import ToolResult


class ParseTool(BaseTool):
    @property
    def name(self) -> str:
        return "parse"

    @property
    def description(self) -> str:
        return "Parse and normalize content"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"content": {"type": "string"}}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        return ToolResult(output={"text": ""})
