"""文档加载器 - 加载本地 PDF/Word/TXT 文档"""

import os
from pathlib import Path
from typing import List, Optional

from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter


class DocumentLoader:
    """加载和处理本地文档"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        初始化文档加载器

        Args:
            chunk_size: 文档分块大小
            chunk_overlap: 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.node_parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    def load_documents(self, doc_dir: str) -> List[Document]:
        """
        加载目录下所有文档

        Args:
            doc_dir: 文档目录路径

        Returns:
            Document 列表
        """
        doc_path = Path(doc_dir)
        if not doc_path.exists():
            raise FileNotFoundError(f"文档目录不存在: {doc_dir}")

        # 支持的文件类型
        supported_extensions = [".pdf", ".docx", ".doc", ".txt", ".md"]

        # 检查是否有支持的文件
        files = [f for f in doc_path.iterdir()
                 if f.is_file() and f.suffix.lower() in supported_extensions]

        if not files:
            print(f"警告: 目录 {doc_dir} 中没有找到支持的文档文件")
            return []

        print(f"找到 {len(files)} 个文档文件")

        # 使用 SimpleDirectoryReader 加载文档
        reader = SimpleDirectoryReader(
            input_dir=doc_dir,
            recursive=False,
            required_exts=supported_extensions
        )

        documents = reader.load_data()

        # 为每个文档添加元数据
        for doc in documents:
            if "file_name" not in doc.metadata:
                doc.metadata["file_name"] = "unknown"
            doc.metadata["source_type"] = "local"

        print(f"成功加载 {len(documents)} 个文档")
        return documents

    def parse_to_nodes(self, documents: List[Document]):
        """
        将文档解析为节点

        Args:
            documents: Document 列表

        Returns:
            节点列表
        """
        if not documents:
            return []

        nodes = self.node_parser.get_nodes_from_documents(documents)

        # 为每个节点添加序号
        for i, node in enumerate(nodes):
            node.metadata["chunk_id"] = f"chunk_{i:04d}"

        print(f"文档已分割为 {len(nodes)} 个文本块")
        return nodes
