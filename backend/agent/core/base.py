from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from backend.agent.core.context import BaseContext, Context
from backend.agent.core.common.exceptions import MaxIterationsExceeded
from backend.agent.core.llm import LLMClient
from backend.agent.core.memory import BaseMemory
from backend.agent.core.common.models import AgentResult, ToolResult
from backend.agent.core.common.events import EventType, AgentBaseEvent, AgentThoughtEvent, AgentActionEvent, AgentResultEvent
from backend.agent.core.tool import BaseTool

class BaseAgent:
    """Base agent with iterative tool-calling loop."""

    def __init__(
        self,
        llm: LLMClient,
        tools: List[BaseTool],
        context_type: Optional[BaseContext] = Context,
        memory_type: Optional[BaseMemory] = None,
        **kwargs: Any,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.context_type = context_type
        self.memory_type = memory_type
        self.force_stop = kwargs.get("force_stop", True)
        self.max_iterations = kwargs.get("max_iterations", 20)
        self.temperature = kwargs.get("temperature", 0.2)

    async def run(self, system_prompt: str, user_prompt: str, context: BaseContext) -> AgentResult:
        """Execute task in batch mode via iter()."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        result: AgentResult | None = None
        async for event in self.iter(messages, context):
            if event.type == EventType.RESULT:
                result = AgentResult(output=event.content)
        if result is None:
            raise MaxIterationsExceeded()
        return result

    async def stream_run(self, system_prompt: str, user_prompt: str, context: BaseContext) -> AsyncIterator[AgentBaseEvent]:
        """Execute task in streaming mode via iter()."""
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        async for event in self.iter(messages, context):
            yield event

    async def iter(
        self, 
        messages: List[Dict[str, Any]] = [], 
        context: BaseContext = None
    ):
        """Iteratively execute the agent with tool calls."""
        tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters_schema,
                },
            }
            for tool in self.tools
        ]
        tool_map = {tool.name: tool for tool in self.tools}

        for iteration in range(self.max_iterations):
            response = self.llm.complete_tools(
                messages=messages,
                tools=tool_schemas,
                temperature=self.temperature,
            )
            assistant_content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if not tool_calls:
                yield AgentResultEvent(
                    type=EventType.RESULT,
                    content=assistant_content,
                    metadata={"iteration": iteration},
                    timestamp=datetime.utcnow(),
                )
                return

            if assistant_content:
                yield AgentThoughtEvent(
                    type=EventType.THOUGHT,
                    content=assistant_content,
                    metadata={"iteration": iteration},
                    timestamp=datetime.utcnow(),
                )

            assistant_message: Dict[str, Any] = {
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": [],
            }

            for call in tool_calls:
                assistant_message["tool_calls"].append(
                    {
                        "id": call["id"],
                        "type": "function",
                        "function": {
                            "name": call["name"],
                            "arguments": call["arguments"],
                        },
                    }
                )

            messages.append(assistant_message)

            for call in tool_calls:
                tool = tool_map.get(call["name"])
                if tool is None:
                    raise ValueError(f"Tool not found: {call['name']}")

                try:
                    tool_args = json.loads(call["arguments"] or "{}")
                except json.JSONDecodeError:
                    tool_args = {}

                yield AgentActionEvent(
                    type=EventType.ACTION,
                    content={"tool_name": tool.name, "tool_args": tool_args},
                    metadata={"iteration": iteration, "tool_call_id": call["id"]},
                    timestamp=datetime.utcnow(),
                )

                tool_result = await tool.execute(**tool_args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(tool_result.output),
                    }
                )
        if self.force_stop:
            response = self.llm.complete(
                messages=messages,
                temperature=self.temperature,
            )
            assistant_content = response.get("content", "")
            yield AgentResultEvent(
                type=EventType.RESULT,
                content=assistant_content,
                metadata={"iteration": iteration, "force_stoped": True},
                timestamp=datetime.utcnow(),
            )
            return

        else:
            raise MaxIterationsExceeded()
