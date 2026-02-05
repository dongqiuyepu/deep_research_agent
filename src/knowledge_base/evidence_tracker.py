"""证据追踪器 - 为检索结果分配证据ID并格式化"""

from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class Evidence:
    """证据数据结构"""
    evidence_id: str
    source: str
    page: int
    content: str
    score: float
    source_type: str  # "local" 或 "web"
    url: str = ""  # 网页来源的URL

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceTracker:
    """证据追踪器"""

    def __init__(self):
        self.evidence_counter = 0
        self.evidence_map: Dict[str, Evidence] = {}

    def reset(self):
        """重置计数器"""
        self.evidence_counter = 0
        self.evidence_map.clear()

    def assign_evidence_id(self) -> str:
        """分配新的证据ID"""
        self.evidence_counter += 1
        return f"EVD-{self.evidence_counter:03d}"

    def create_evidence_from_local(
        self,
        node_with_score,
        evidence_id: str = None
    ) -> Evidence:
        """
        从本地检索结果创建证据

        Args:
            node_with_score: LlamaIndex NodeWithScore 对象
            evidence_id: 可选的证据ID，不提供则自动分配

        Returns:
            Evidence 对象
        """
        if evidence_id is None:
            evidence_id = self.assign_evidence_id()

        node = node_with_score.node
        metadata = node.metadata

        evidence = Evidence(
            evidence_id=evidence_id,
            source=metadata.get("file_name", "未知文档"),
            page=metadata.get("page_label", metadata.get("page", 0)),
            content=node.get_content(),  # 不再限制内容长度
            score=round(node_with_score.score,
                        4) if node_with_score.score else 0.0,
            source_type="local"
        )

        self.evidence_map[evidence_id] = evidence
        return evidence

    def create_evidence_from_web(
        self,
        title: str,
        content: str,
        url: str,
        score: float = 0.0,
        evidence_id: str = None
    ) -> Evidence:
        """
        从网页搜索结果创建证据

        Args:
            title: 网页标题
            content: 网页内容摘要
            url: 网页URL
            score: 相关性分数
            evidence_id: 可选的证据ID

        Returns:
            Evidence 对象
        """
        if evidence_id is None:
            evidence_id = self.assign_evidence_id()

        evidence = Evidence(
            evidence_id=evidence_id,
            source=title,
            page=0,
            content=content,  # 不再限制内容长度
            score=round(score, 4),
            source_type="web",
            url=url
        )

        self.evidence_map[evidence_id] = evidence
        return evidence

    def format_evidence_for_prompt(self, evidences: List[Evidence]) -> str:
        """
        格式化证据列表用于 Prompt

        Args:
            evidences: 证据列表

        Returns:
            格式化的字符串
        """
        if not evidences:
            return "（未找到相关证据）"

        lines = []
        for e in evidences:
            source_info = f"[{e.evidence_id}] "
            if e.source_type == "local":
                source_info += f"来源: {e.source}"
                if e.page:
                    source_info += f" (第{e.page}页)"
            else:
                source_info += f"来源: {e.source} (网页)"

            lines.append(source_info)
            lines.append(f"内容: {e.content}")
            lines.append("")

        return "\n".join(lines)

    def format_evidence_chain(self, evidences: List[Evidence]) -> str:
        """
        格式化证据链用于输出展示

        Args:
            evidences: 证据列表

        Returns:
            格式化的证据链字符串
        """
        if not evidences:
            return "（无证据）"

        lines = []
        for e in evidences:
            # 来源类型标识
            type_label = "本地" if e.source_type == "local" else "网页"

            # 来源信息
            if e.source_type == "local":
                source_detail = f"{e.source}"
                if e.page:
                    source_detail += f" 第{e.page}页"
            else:
                source_detail = f"{e.source}"

            lines.append(f"[{e.evidence_id}] {type_label} | {source_detail}")

            # 内容预览（截取前100字符）
            preview = e.content[:100].replace("\n", " ")
            if len(e.content) > 100:
                preview += "..."
            lines.append(f"  \"{preview}\"")

            # 网页URL
            if e.url:
                lines.append(f"  URL: {e.url}")

            lines.append("")

        return "\n".join(lines)

    def get_evidence(self, evidence_id: str) -> Evidence:
        """根据ID获取证据"""
        return self.evidence_map.get(evidence_id)

    def get_all_evidence(self) -> List[Evidence]:
        """获取所有证据"""
        return list(self.evidence_map.values())
