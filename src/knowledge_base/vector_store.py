"""向量存储 - 使用 Chroma 存储和检索文档向量"""

import os
from pathlib import Path
from typing import List, Optional

import chromadb
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import NodeWithScore
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()


def get_embedding_model():
    """获取 Dashscope text-embedding-v3 模型"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DASHSCOPE_BASE_URL",
                         "https://dashscope.aliyuncs.com/compatible-mode/v1")

    return DashScopeEmbedding(
        model_name="text-embedding-v3",
        api_key=api_key,
        base_url=base_url,
        embed_batch_size=5  # Dashscope 限制每批最多10个
    )


class VectorStore:
    """Chroma 向量存储封装"""

    def __init__(self, persist_dir: str = "./data/chroma_db", collection_name: str = "policy_docs"):
        """
        初始化向量存储

        Args:
            persist_dir: 持久化目录
            collection_name: 集合名称
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.index: Optional[VectorStoreIndex] = None

        # 确保持久化目录存在
        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        # 初始化 Chroma 客户端
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)

    def build_index(self, nodes: List) -> VectorStoreIndex:
        """
        从节点构建索引

        Args:
            nodes: 文档节点列表

        Returns:
            VectorStoreIndex
        """
        if not nodes:
            raise ValueError("节点列表为空，无法构建索引")

        # 获取或创建集合
        collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )

        # 创建向量存储
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store)

        # 获取 embedding 模型
        embed_model = get_embedding_model()

        # 构建索引
        self.index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            embed_model=embed_model
        )

        print(f"索引构建完成，共 {len(nodes)} 个节点")
        return self.index

    def load_index(self) -> Optional[VectorStoreIndex]:
        """
        加载已有索引

        Returns:
            VectorStoreIndex 或 None
        """
        try:
            # 获取集合
            collection = self.chroma_client.get_collection(
                name=self.collection_name
            )

            # 检查集合是否有数据
            if collection.count() == 0:
                print("集合为空，需要重新构建索引")
                return None

            # 创建向量存储
            vector_store = ChromaVectorStore(chroma_collection=collection)

            # 获取 embedding 模型
            embed_model = get_embedding_model()

            # 从向量存储创建索引
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embed_model
            )

            print(f"索引加载成功，集合中有 {collection.count()} 个文档")
            return self.index

        except Exception as e:
            print(f"加载索引失败: {e}")
            return None

    def query(self, query_text: str, top_k: int = 5) -> List[NodeWithScore]:
        """
        检索相关文档

        Args:
            query_text: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if self.index is None:
            raise ValueError("索引未初始化，请先构建或加载索引")

        # 创建检索器
        retriever = self.index.as_retriever(similarity_top_k=top_k)

        # 执行检索
        results = retriever.retrieve(query_text)

        return results

    def clear_index(self):
        """清除索引"""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.index = None
            print("索引已清除")
        except Exception as e:
            print(f"清除索引失败: {e}")
