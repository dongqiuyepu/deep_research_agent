# 队列式问题分解策略实现方案

## 一、设计目标

采用类似 AutoGPT 的任务队列方式，实现显式的问题分解和进度追踪：

```
原始问题 → decompose 分解 → 子任务入队 → 按序处理 → resolve_task 完成 → 队列清空 → finish 总结
```

**核心优势**：
- 子任务有明确状态：`pending` → `in_progress` → `resolved`
- 证据与子任务显式关联
- LLM 通过结构化队列状态感知进度
- 队列清空作为触发总结的明确信号

**设计选择**：
- **处理顺序**：FIFO（先入先出），按分解顺序依次处理
- **分解层级**：单层分解，子任务不可再分解（简化实现，避免复杂度爆炸）

---

## 二、数据结构设计

### 2.1 SubTask 数据类

```python
# src/agent/task_queue.py

@dataclass
class SubTask:
    task_id: str                           # TASK-001, TASK-002, ...
    question: str                          # 子问题文本
    parent_task_id: str                    # 父任务ID（ROOT 为根任务）
    status: str                            # "pending" | "in_progress" | "resolved"
    created_at: int                        # 创建时的迭代轮次
    started_at: Optional[int] = None       # 开始处理时的轮次
    resolved_at: Optional[int] = None      # 完成时的轮次
    answer: Optional[str] = None           # 子任务答案
    evidence_ids: List[str] = field(default_factory=list)  # 关联证据
```

### 2.2 TaskQueue 类

```python
class TaskQueue:
    """任务队列管理器"""
    
    def __init__(self):
        self.queue: List[SubTask] = []           # 待处理队列
        self.completed_tasks: List[SubTask] = [] # 已完成任务
        self.task_counter: int = 0               # ID计数器
        self.current_task: Optional[SubTask] = None  # 当前聚焦任务
    
    # 核心方法
    def enqueue(question, parent_id, iteration) -> SubTask  # 入队
    def dequeue() -> Optional[SubTask]                      # 出队并开始
    def resolve_current(answer, evidence_ids, iteration)    # 完成当前任务
    def add_evidence_to_current(evidence_ids)               # 关联证据
    def get_queue_summary() -> str                          # 生成状态摘要
    def is_all_resolved() -> bool                           # 是否全部完成
```

---

## 三、工具层改造

### 3.1 新增 ResolveTaskTool

```python
# src/tools/research_tools.py

class ResolveTaskTool(BaseTool):
    name = "resolve_task"
    description = "标记当前子任务已完成，提供该子任务的答案和置信度"
    parameters = {
        "properties": {
            "answer": {"type": "string", "description": "子任务的答案"},
            "confidence": {"type": "number", "description": "答案置信度(0-1)"}
        },
        "required": ["answer"]
    }
```

### 3.2 更新工具注册

在 `create_research_tools()` 中添加 `ResolveTaskTool()`

---

## 四、ReActEngine 集成

### 4.1 初始化

```python
# src/agent/react_engine.py

class ReActEngine:
    def __init__(self, llm_client, tool_registry, max_iterations=10):
        # ... 现有代码 ...
        self.task_queue = TaskQueue()  # 新增
```

### 4.2 run() 方法改造

**入口处理**：
```python
def run(self, question: str, memory_history=None):
    # 将原始问题作为根任务入队
    self.task_queue.enqueue(question, parent_id="ROOT", iteration=0)
    self.task_queue.dequeue()  # 立即开始处理
```

**工具执行后钩子**：

```python
# decompose 工具：子问题入队
if tool_name == "decompose" and result.success:
    for sub_q in result.data["sub_questions"]:
        self.task_queue.enqueue(
            question=sub_q,
            parent_id=self.task_queue.current_task.task_id,
            iteration=iteration
        )

# 搜索工具：证据关联到当前任务
if tool_name in ["kb_search", "web_search"] and result.success:
    evidence_ids = result.metadata.get("ids", [])
    if evidence_ids and self.task_queue.current_task:
        self.task_queue.add_evidence_to_current(evidence_ids)

# resolve_task 工具：完成当前任务并切换
if tool_name == "resolve_task" and result.success:
    self.task_queue.resolve_current(
        answer=result.data["answer"],
        evidence_ids=self.task_queue.current_task.evidence_ids,
        iteration=iteration
    )
    # 尝试获取下一个任务
    if not self.task_queue.is_empty():
        self.task_queue.dequeue()
```

**终止条件**：
```python
# finish 工具：检查是否所有任务完成
if tool_name == "finish" and result.success:
    if self.task_queue.is_all_resolved():
        # 研究完成
        return {..., "status": "completed"}
    else:
        # 还有未完成任务，继续循环
        continue
```

---

## 五、Prompt 增强

### 5.1 队列状态注入

```python
REACT_SYSTEM_PROMPT = """...

## 任务分解与队列管理
- 使用 decompose 工具将复杂问题分解为子问题（自动入队）
- 使用 resolve_task 工具标记当前子任务完成（自动切换到下一个）
- 所有子任务完成后，使用 finish 工具生成综合性答案

{queue_status}

## 当前聚焦任务
{current_task_info}

..."""
```

### 5.2 队列状态示例

```
=== 任务队列状态 ===
当前任务: [TASK-002] 客户数据有哪些使用限制？ (in_progress)
  已收集证据: 2 条

待处理队列 (2):
  - [TASK-003] 模型训练需要什么授权？
  - [TASK-004] 如何保护客户隐私？

已完成任务 (1):
  ✓ [TASK-001] 银行能否使用客户数据训练大模型？
```

---

## 六、文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/agent/task_queue.py` | **新建** | SubTask 和 TaskQueue 数据结构 |
| `src/tools/research_tools.py` | 修改 | 添加 ResolveTaskTool |
| `src/agent/react_engine.py` | 修改 | 集成 TaskQueue，添加钩子逻辑，增强 Prompt |
| `src/agent/research_agent.py` | 修改 | 报告生成时展示任务树 |

---

## 七、实施步骤

### 步骤 1：创建 task_queue.py

1. 定义 `SubTask` dataclass
2. 实现 `TaskQueue` 类核心方法
3. 实现 `get_queue_summary()` 格式化输出

### 步骤 2：添加 ResolveTaskTool

1. 在 `research_tools.py` 中定义工具类
2. 在 `create_research_tools()` 中注册

### 步骤 3：集成到 ReActEngine

1. 在 `__init__` 中初始化 `TaskQueue`
2. 在 `run()` 入口将原始问题入队
3. 添加 decompose 工具后的入队逻辑
4. 添加搜索工具后的证据关联逻辑
5. 添加 resolve_task 后的任务切换逻辑
6. 修改终止条件判断

### 步骤 4：Prompt 增强

1. 修改 `REACT_SYSTEM_PROMPT` 模板
2. 在 Prompt 构建时注入队列状态
3. 添加子任务答案汇总供 finish 使用

### 步骤 5：报告生成扩展（可选）

1. 在报告中展示任务树结构
2. 按任务分组展示证据链

---

## 八、验证方案

### 测试用例

```bash
python main.py
# 输入: /research 银行能否使用客户数据训练大模型？
```

### 预期行为

1. LLM 调用 `decompose` 分解为 3 个子问题
2. 控制台显示"已将 3 个子问题加入队列"
3. 每轮 Prompt 中显示队列状态
4. LLM 依次处理每个子任务，调用 `resolve_task` 完成
5. 队列清空后，LLM 调用 `finish` 生成总结
6. 报告中包含任务完成统计

### 成功标准

- [ ] 子问题正确入队
- [ ] 证据正确关联到对应子任务
- [ ] LLM 能理解队列状态并按顺序处理
- [ ] 队列清空后触发总结
- [ ] 报告中体现任务树结构

---

## 九、与现有架构的兼容性

- **不使用 decompose 时**：队列只包含根任务，行为与现有完全一致
- **现有工具无需修改**：kb_search、web_search、evaluate、finish 保持原有接口
- **渐进式启用**：可通过配置开关控制是否使用队列模式
