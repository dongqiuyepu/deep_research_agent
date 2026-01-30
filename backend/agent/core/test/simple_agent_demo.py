from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Allow running from repo root or backend/ without installing the package.
CURRENT_DIR = Path(__file__).resolve()
REPO_ROOT = CURRENT_DIR.parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.agent.core.base import BaseAgent
from backend.agent.core.common.models import ToolResult
from backend.agent.core.context import Context
from backend.agent.core.tool import BaseTool


class AddTool(BaseTool):
    @property
    def name(self) -> str:
        return "add"

    @property
    def description(self) -> str:
        return "Add two numbers"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        }

    async def execute(self, **kwargs: Any) -> ToolResult:
        a = kwargs.get("a", 0)
        b = kwargs.get("b", 0)
        return ToolResult(output={"sum": a + b})


class DummyLLM:
    """Deterministic LLM stub that triggers a tool call then returns a final answer."""

    def __init__(self) -> None:
        self.step = 0

    def complete_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if self.step == 0:
            self.step += 1
            return {
                "content": "I will add two numbers.",
                "tool_calls": [
                    {
                        "id": "call_add_1",
                        "name": "add",
                        "arguments": json.dumps({"a": 2, "b": 3}),
                    }
                ],
            }
        return {"content": "The sum is 5.", "tool_calls": []}

    def complete(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
    ) -> str:
        return "Forced stop reached."


async def main() -> None:
    agent = BaseAgent(
        llm=DummyLLM(),
        tools=[AddTool()],
        max_iterations=5,
        force_stop=True,
    )
    context = Context()
    async for event in agent.stream_run(
        system_prompt="You are a helpful agent.",
        user_prompt="Add 2 and 3.",
        context=context,
    ):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
