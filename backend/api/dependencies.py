from __future__ import annotations

from backend.agent.agents.query_generator import QueryGeneratorAgent
from backend.agent.tools.fetch_tool import FetchTool
from backend.agent.tools.parse_tool import ParseTool
from backend.agent.tools.search_tool import SearchTool
from backend.provider.llm.openai_provider import OpenAIProvider


def get_query_generator() -> QueryGeneratorAgent:
    llm = OpenAIProvider()
    tools = [SearchTool(), FetchTool(), ParseTool()]
    return QueryGeneratorAgent(name="query_generator", llm_provider=llm, tools=tools)
