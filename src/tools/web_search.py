"""网页搜索工具 - 使用 Tavily API"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class WebSearchResult:
    """网页搜索结果"""
    title: str
    content: str
    url: str
    score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "score": self.score
        }


class WebSearchTool:
    """Tavily 网页搜索工具"""

    def __init__(self, api_key: str = None):
        """
        初始化网页搜索工具

        Args:
            api_key: Tavily API Key，不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.client = None
        self._initialized = False

        if self.api_key:
            self._init_client()

    def _init_client(self):
        """初始化 Tavily 客户端"""
        try:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=self.api_key)
            self._initialized = True
            print("Tavily 搜索工具初始化成功")
        except ImportError:
            print("警告: tavily-python 未安装，网页搜索功能不可用")
            print("请运行: pip install tavily-python")
        except Exception as e:
            print(f"Tavily 初始化失败: {e}")

    def is_available(self) -> bool:
        """检查搜索工具是否可用"""
        return self._initialized and self.client is not None

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic"
    ) -> List[WebSearchResult]:
        """
        执行网页搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数量
            search_depth: 搜索深度 ("basic" 或 "advanced")

        Returns:
            搜索结果列表
        """
        if not self.is_available():
            print("网页搜索不可用")
            return []

        try:
            print(f"正在搜索: {query}")

            # 调用 Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_answer=False,
                include_raw_content=False
            )

            # 解析结果
            results = []
            for item in response.get("results", []):
                result = WebSearchResult(
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    url=item.get("url", ""),
                    score=item.get("score", 0.0)
                )
                results.append(result)

            print(f"搜索完成，找到 {len(results)} 条结果")
            return results

        except Exception as e:
            print(f"搜索失败: {e}")
            return []

    def search_with_context(
        self,
        query: str,
        context: str = "",
        max_results: int = 5
    ) -> List[WebSearchResult]:
        """
        带上下文的搜索（优化查询）

        Args:
            query: 原始查询
            context: 上下文信息
            max_results: 最大结果数量

        Returns:
            搜索结果列表
        """
        # 如果有上下文，可以优化查询
        enhanced_query = query
        if context:
            # 简单的查询增强：添加关键词
            enhanced_query = f"{query} {context[:100]}"

        return self.search(enhanced_query, max_results=max_results)

    def format_results_for_prompt(self, results: List[WebSearchResult]) -> str:
        """
        格式化搜索结果用于 Prompt

        Args:
            results: 搜索结果列表

        Returns:
            格式化的字符串
        """
        if not results:
            return "（未找到相关网页信息）"

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[网页{i}] {r.title}")
            lines.append(f"内容: {r.content[:300]}")
            lines.append(f"来源: {r.url}")
            lines.append("")

        return "\n".join(lines)
