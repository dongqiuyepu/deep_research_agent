# Deep Research Demo 实现计划

## 目标
构建一个基于 LlamaIndex + Chroma 的政策合规研究 Demo，支持 RAG 问答和证据链追溯。

## 技术架构

```
用户输入 → ResearchAgent → 知识库检索(Chroma) → LLM生成(通义千问) → 带证据链的结果
                ↓
          ConversationMemory (对话历史)
```

## 核心依赖
```
llama-index>=0.10.0
llama-index-vector-stores-chroma>=0.1.0
chromadb>=0.4.22
pypdf>=3.17.0
python-docx>=1.1.0
```

---

## 实现步骤

### 阶段一：知识库模块 (knowledge_base/)

**1. 创建 `src/knowledge_base/document_loader.py`**
- 功能：加载 PDF/Word/TXT 文档
- 使用 LlamaIndex `SimpleDirectoryReader`
- 设置分块参数：chunk_size=512, chunk_overlap=50
- 为每个文档块添加元数据（文件名、页码）

**2. 创建 `src/knowledge_base/vector_store.py`**
- 功能：Chroma 向量存储封装
- 初始化 ChromaVectorStore，持久化到 `data/chroma_db/`
- 实现 `build_index()` 和 `load_index()` 方法

**3. 创建 `src/knowledge_base/retriever.py`**
- 功能：语义检索
- 配置 similarity_top_k=5
- 返回检索结果 + 相似度分数 + 元数据

**4. 创建 `src/knowledge_base/evidence_tracker.py`**
- 功能：证据追踪
- 为每个检索结果分配唯一 evidence_id（EVD-001 格式）
- 结构化证据信息：{id, source_file, page, content, score}

**5. 创建 `src/knowledge_base/manager.py`**
- 功能：统一入口
- 方法：
  - `initialize(doc_dir)` - 加载文档并构建索引
  - `search(query, top_k)` - 检索并返回带证据的结果

### 阶段二：记忆模块 (memory/)

**1. 创建 `src/memory/conversation_memory.py`**
- 功能：简单对话历史
- 方法：
  - `add_message(role, content)`
  - `get_history()`
  - `get_recent(n)`
  - `clear()`

### 阶段三：Agent 模块 (agent/)

**1. 创建 `src/agent/prompt_builder.py`**
- 系统 Prompt 模板（合规研究专家角色）
- RAG Prompt 模板（注入检索证据，要求 [EVD-XXX] 引用格式）
- 示例格式：
  ```
  【证据】
  [EVD-001] 来源: xxx.pdf 第12页
  内容: ...
  
  【问题】
  ...
  
  【要求】
  每个结论后用 [EVD-XXX] 标注来源
  ```

**2. 创建 `src/agent/research_agent.py`**
- 核心类：`ResearchAgent`
- 构造函数：`__init__(llm, kb_manager, memory)`
- 主方法：`research(question)` 返回 `{answer, evidence_chain}`
- 流程：
  1. 调用 kb_manager.search() 检索相关证据
  2. 使用 prompt_builder 构建 RAG Prompt
  3. 调用 llm.chat() 生成答案
  4. 解析答案中的 [EVD-XXX] 引用
  5. 返回结构化结果

### 阶段四：主流程改造

**1. 修改 `src/main.py`**
- 初始化：
  ```python
  kb_manager = KnowledgeBaseManager()
  kb_manager.initialize("data/documents")
  memory = ConversationMemory()
  agent = ResearchAgent(llm, kb_manager, memory)
  ```
- 对话循环改造：
  ```python
  result = agent.research(user_question)
  # 输出答案 + 证据链
  ```

**2. 创建 `data/documents/` 目录**
- 放入政策法规文档（PDF/Word）

### 阶段五：测试验证

**测试场景：**
1. 银行是否可以用客户数据训练大模型？
2. 自动授信是否需要人工干预？
3. 大模型对话日志保存多久？

**验证点：**
- 能正常检索到相关法规条文
- 答案包含 [EVD-XXX] 证据引用
- 证据链可追溯到具体文档和页码

---

## 文件结构

```
deep_research_agent-main/
├── data/
│   ├── documents/          # 政策法规文档（用户提供）
│   └── chroma_db/          # Chroma 向量库（自动生成）
├── src/
│   ├── main.py             # 主流程（改造）
│   ├── llm.py              # LLM客户端（保持不变）
│   ├── knowledge_base/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── document_loader.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── evidence_tracker.py
│   ├── memory/
│   │   ├── __init__.py
│   │   └── conversation_memory.py
│   └── agent/
│       ├── __init__.py
│       ├── research_agent.py
│       └── prompt_builder.py
└── requirements.txt        # 更新依赖
```

---

## 关键实现要点

### 1. 证据追溯机制
- 每个文档块在索引时添加唯一 chunk_id
- 检索时为结果分配 evidence_id
- Prompt 中要求 LLM 使用 [EVD-XXX] 格式引用
- 后处理提取引用，构建完整证据链

### 2. LlamaIndex + Chroma 集成
```python
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# 初始化 Chroma
chroma_client = chromadb.PersistentClient(path="./data/chroma_db")
collection = chroma_client.get_or_create_collection("policy_docs")
vector_store = ChromaVectorStore(chroma_collection=collection)
```

### 3. 通义千问 API 兼容
- 现有 llm.py 无需改动（已支持 OpenAI 兼容接口）
- 嵌入模型：可使用 LlamaIndex 默认嵌入或通义千问 text-embedding-v3

---

## 预期输出示例

```
=== 研究结论 ===
【回答】
不允许直接使用。银行必须满足：
1. 数据匿名化处理 [EVD-001]
2. 获得客户单独同意 [EVD-002]
3. 建立训练专用数据隔离区 [EVD-003]

=== 证据链 ===
[EVD-001] 《银行业数据治理指引》第18条
  "客户信息用于建模时应进行脱敏处理..."

[EVD-002] 《个人信息保护法》第13条
  "超出原处理目的需另行取得同意..."

[EVD-003] 《金融科技发展规划》
  "推荐建立训练专用数据域..."
```

---

## 验证方式
1. 安装依赖：`pip install -r requirements.txt`
2. 准备测试文档放入 `data/documents/`
3. 运行：`cd src && python main.py`
4. 输入测试问题，验证答案和证据链
