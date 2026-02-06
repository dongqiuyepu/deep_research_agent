"""研究工具集 - 封装搜索、分析、生成类工具"""

from typing import Dict, List, Any
from tools.base_tool import BaseTool, ToolResult


class KBSearchTool(BaseTool):
    """知识库搜索工具"""

    name = "kb_search"
    description = "从本地知识库检索相关文档和证据"
    parameters = {
        "properties": {
            "query": {"type": "string", "description": "搜索查询关键词"}
        },
        "required": ["query"]
    }

    def __init__(self, kb_manager):
        self.kb_manager = kb_manager

    def execute(self, query: str, top_k: int = 5) -> ToolResult:
        evidences, evidence_text = self.kb_manager.search(
            query=query, top_k=top_k)

        if not evidences:
            return ToolResult(
                success=True,
                data={"evidences": [], "text": "未找到相关证据"},
                metadata={"count": 0}
            )

        evidence_ids = [e.evidence_id for e in evidences]
        return ToolResult(
            success=True,
            data={"evidences": evidences, "text": evidence_text},
            metadata={"count": len(evidences), "ids": evidence_ids}
        )


class WebSearchTool(BaseTool):
    """网页搜索工具"""

    name = "web_search"
    description = "搜索互联网获取最新信息和外部证据"
    parameters = {
        "properties": {
            "query": {"type": "string", "description": "搜索查询关键词"}
        },
        "required": ["query"]
    }

    def __init__(self, web_search, kb_manager):
        self.web_search = web_search
        self.kb_manager = kb_manager

    def execute(self, query: str, max_results: int = 3) -> ToolResult:
        if not self.web_search.is_available():
            return ToolResult(success=False, error="网页搜索不可用")

        results = self.web_search.search(query, max_results=max_results)

        if not results:
            return ToolResult(
                success=True,
                data={"evidences": [], "text": "未找到相关网页"},
                metadata={"count": 0}
            )

        # 转换为证据格式
        evidences = []
        for r in results:
            evidence = self.kb_manager.add_web_evidence(
                title=r.title,
                content=r.content,
                url=r.url,
                score=r.score
            )
            evidences.append(evidence)

        evidence_ids = [e.evidence_id for e in evidences]
        evidence_text = self._format_evidences(evidences)

        return ToolResult(
            success=True,
            data={"evidences": evidences, "text": evidence_text},
            metadata={"count": len(evidences), "ids": evidence_ids}
        )

    def _format_evidences(self, evidences) -> str:
        lines = []
        for e in evidences:
            lines.append(f"[{e.evidence_id}] {e.source} (网页)")
            lines.append(f"内容: {e.content}")
            lines.append("")
        return "\n".join(lines)


class DecomposeTool(BaseTool):
    """问题分解工具 - 将复杂问题拆解为子问题"""

    name = "decompose"
    description = "将复杂问题分解为更小的子问题，便于逐个研究"
    parameters = {
        "properties": {
            "question": {"type": "string", "description": "需要分解的复杂问题"},
            "sub_questions": {"type": "array", "description": "分解后的子问题列表"}
        },
        "required": ["question", "sub_questions"]
    }

    def execute(self, question: str, sub_questions: List[str]) -> ToolResult:
        return ToolResult(
            success=True,
            data={
                "original": question,
                "sub_questions": sub_questions,
                "count": len(sub_questions)
            },
            metadata={"action": "decompose"}
        )


class EvaluateTool(BaseTool):
    """证据评估工具 - 评估当前收集的证据是否充分"""

    name = "evaluate"
    description = "评估当前收集的证据质量和充分性，决定是否需要继续搜索"
    parameters = {
        "properties": {
            "assessment": {"type": "string", "description": "对证据的评估说明"},
            "is_sufficient": {"type": "boolean", "description": "证据是否充分"}
        },
        "required": ["assessment", "is_sufficient"]
    }

    def execute(self, assessment: str, is_sufficient: bool) -> ToolResult:
        return ToolResult(
            success=True,
            data={
                "assessment": assessment,
                "is_sufficient": is_sufficient
            },
            metadata={"action": "evaluate"}
        )


class FinishTool(BaseTool):
    """完成工具 - 标记研究完成并返回最终答案"""

    name = "finish"
    description = "当证据足够时调用此工具，生成最终研究答案"
    parameters = {
        "properties": {
            "answer": {"type": "string", "description": "基于证据的最终答案，需引用[EVD-XXX]"},
            "confidence": {"type": "number", "description": "答案置信度(0-1)"}
        },
        "required": ["answer"]
    }

    def execute(self, answer: str, confidence: float = 0.8) -> ToolResult:
        return ToolResult(
            success=True,
            data={
                "answer": answer,
                "confidence": confidence,
                "is_final": True
            },
            metadata={"action": "finish"}
        )


class ResolveTaskTool(BaseTool):
    """任务完成工具 - 标记当前子任务已解决"""

    name = "resolve_task"
    description = "标记当前子任务已完成，提供该子任务的答案"
    parameters = {
        "properties": {
            "answer": {"type": "string", "description": "子任务的答案，需引用[EVD-XXX]"},
            "confidence": {"type": "number", "description": "答案置信度(0-1)"}
        },
        "required": ["answer"]
    }

    def execute(self, answer: str, confidence: float = 0.8) -> ToolResult:
        return ToolResult(
            success=True,
            data={
                "answer": answer,
                "confidence": confidence
            },
            metadata={"action": "resolve_task"}
        )


def create_research_tools(kb_manager, web_search) -> List[BaseTool]:
    """创建所有研究工具"""
    return [
        KBSearchTool(kb_manager),
        WebSearchTool(web_search, kb_manager),
        DecomposeTool(),
        EvaluateTool(),
        ResolveTaskTool(),
        FinishTool()
    ]
