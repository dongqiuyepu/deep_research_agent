import json
from typing import Dict, Any, List
from openai import OpenAI

class LLMClient:
    """Client for interacting with LLMs."""

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        self.model = model

    def complete(
            self, 
            messages: List[Dict[str, Any]],
            temperature: float = 0.2
        ) -> str:
        """Complete a prompt using the LLM."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=1500,
        )
        return response.choices[0].message.content

    def complete_json(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Complete a prompt and parse the first JSON object from the response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={
                'type': 'json_object'
            },
            temperature=temperature,
            max_tokens=1500,
        )
        return json.loads(response.choices[0].message.content)

    def complete_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Call the LLM with tool definitions and return normalized message data."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=1500,
        )
        message = response.choices[0].message
        tool_calls = []
        for call in message.tool_calls or []:
            tool_calls.append(
                {
                    "id": call.id,
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                }
            )
        return {"content": message.content or "", "tool_calls": tool_calls}
