"""知识库管理器 - 统一入口"""

import os
from pathlib import Path
from typing import List, Optional, Tuple

from .document_loader import DocumentLoader
from .vector_store import VectorStore
from .evidence_tracker import EvidenceTracker, Evidence


class KnowledgeBaseManager:
    """知识库管理器 - 整合文档加载、向量存储和证据追踪"""

    def __init__(
        self,
        persist_dir: str = "./data/chroma_db",
        collection_name: str = "policy_docs",
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """
        初始化知识库管理器

        Args:
            persist_dir: 向量库持久化目录
            collection_name: 集合名称
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
        """
        self.document_loader = DocumentLoader(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.vector_store = VectorStore(
            persist_dir=persist_dir,
            collection_name=collection_name
        )
        self.evidence_tracker = EvidenceTracker()
        self.is_initialized = False

    def initialize(self, doc_dir: str, force_rebuild: bool = False) -> bool:
        """
        初始化知识库

        Args:
            doc_dir: 文档目录路径
            force_rebuild: 是否强制重建索引

        Returns:
            是否成功初始化
        """
        print(f"正在初始化知识库...")

        # 尝试加载已有索引
        if not force_rebuild:
            index = self.vector_store.load_index()
            if index is not None:
                print("使用已有索引")
                self.is_initialized = True
                return True

        # 检查文档目录
        doc_path = Path(doc_dir)
        if not doc_path.exists():
            print(f"文档目录不存在: {doc_dir}")
            print("创建空目录，请添加文档后重新初始化")
            doc_path.mkdir(parents=True, exist_ok=True)
            return False

        # 加载文档
        try:
            documents = self.document_loader.load_documents(doc_dir)
            if not documents:
                print("未找到文档，知识库为空")
                self.is_initialized = True  # 允许空知识库
                return True

            # 解析为节点
            nodes = self.document_loader.parse_to_nodes(documents)

            # 构建索引
            self.vector_store.build_index(nodes)

            self.is_initialized = True
            print("知识库初始化完成")
            return True

        except Exception as e:
            print(f"知识库初始化失败: {e}")
            return False

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> Tuple[List[Evidence], str]:
        """
        搜索知识库

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            (证据列表, 格式化的证据文本)
        """
        # 重置证据追踪器
        self.evidence_tracker.reset()

        if not self.is_initialized:
            print("知识库未初始化")
            return [], ""

        # 检查索引是否可用
        if self.vector_store.index is None:
            print("索引为空，无法检索")
            return [], ""

        try:
            # 执行检索
            results = self.vector_store.query(query, top_k=top_k)

            if not results:
                print("未找到相关文档")
                return [], ""

            # 转换为证据格式
            evidences = []
            for result in results:
                evidence = self.evidence_tracker.create_evidence_from_local(
                    result)
                evidences.append(evidence)

            # 格式化为 Prompt 文本
            evidence_text = self.evidence_tracker.format_evidence_for_prompt(
                evidences)

            print(f"检索到 {len(evidences)} 条相关证据")
            return evidences, evidence_text

        except Exception as e:
            print(f"检索失败: {e}")
            return [], ""

    def add_web_evidence(
        self,
        title: str,
        content: str,
        url: str,
        score: float = 0.0
    ) -> Evidence:
        """
        添加网页搜索证据（用于与网页搜索结果合并）

        Args:
            title: 网页标题
            content: 内容摘要
            url: 网页URL
            score: 相关性分数

        Returns:
            Evidence 对象
        """
        return self.evidence_tracker.create_evidence_from_web(
            title=title,
            content=content,
            url=url,
            score=score
        )

    def get_evidence_chain(self) -> str:
        """获取格式化的证据链"""
        evidences = self.evidence_tracker.get_all_evidence()
        return self.evidence_tracker.format_evidence_chain(evidences)

    def get_all_evidence(self) -> List[Evidence]:
        """获取所有证据"""
        return self.evidence_tracker.get_all_evidence()

    def rebuild_index(self, doc_dir: str) -> bool:
        """重建索引"""
        print("正在重建索引...")
        self.vector_store.clear_index()
        return self.initialize(doc_dir, force_rebuild=True)
