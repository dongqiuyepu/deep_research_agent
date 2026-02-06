# 队列式问题分解实现计划

## 概述

采用 AutoGPT 风格的任务队列实现问题分解，使用 FIFO 顺序、单层分解策略。

## 关键文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/agent/task_queue.py` | **新建** | SubTask 数据类 + TaskQueue 管理器 |
| `src/tools/research_tools.py` | 修改 | 添加 ResolveTaskTool，更新 create_research_tools() |
| `src/agent/react_engine.py` | 修改 | 集成 TaskQueue，添加钩子逻辑，增强 Prompt |

---

## 步骤 1：创建 task_queue.py

**路径**: `src/agent/task_queue.py`

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class SubTask:
    task_id: str                           # TASK-001
    question: str                          # 子问题文本
    parent_task_id: str                    # 父任务ID（ROOT 为根任务）
    status: str                            # "pending" | "in_progress" | "resolved"
    created_at: int                        # 创建时的迭代轮次
    started_at: Optional[int] = None
    resolved_at: Optional[int] = None
    answer: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)

class TaskQueue:
    def __init__(self):
        self.queue: List[SubTask] = []
        self.completed_tasks: List[SubTask] = []
        self.task_counter: int = 0
        self.current_task: Optional[SubTask] = None

    def enqueue(self, question: str, parent_id: str, iteration: int) -> SubTask:
        self.task_counter += 1
        task = SubTask(
            task_id=f"TASK-{self.task_counter:03d}",
            question=question,
            parent_task_id=parent_id,
            status="pending",
            created_at=iteration
        )
        self.queue.append(task)
        return task

    def dequeue(self) -> Optional[SubTask]:
        if not self.queue:
            return None
        task = self.queue.pop(0)
        task.status = "in_progress"
        task.started_at = task.created_at  # 或传入当前 iteration
        self.current_task = task
        return task

    def resolve_current(self, answer: str, evidence_ids: List[str], iteration: int):
        if self.current_task:
            self.current_task.status = "resolved"
            self.current_task.answer = answer
            self.current_task.evidence_ids = evidence_ids
            self.current_task.resolved_at = iteration
            self.completed_tasks.append(self.current_task)
            self.current_task = None

    def add_evidence_to_current(self, evidence_ids: List[str]):
        if self.current_task:
            self.current_task.evidence_ids.extend(evidence_ids)

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    def is_all_resolved(self) -> bool:
        return self.is_empty() and len(self.completed_tasks) > 0

    def get_queue_summary(self) -> str:
        lines = ["=== 任务队列状态 ==="]
        
        if self.current_task:
            lines.append(f"当前任务: [{self.current_task.task_id}] {self.current_task.question}")
            lines.append(f"  已收集证据: {len(self.current_task.evidence_ids)} 条")
        
        if self.queue:
            lines.append(f"\n待处理队列 ({len(self.queue)}):")
            for t in self.queue:
                lines.append(f"  - [{t.task_id}] {t.question}")
        
        if self.completed_tasks:
            lines.append(f"\n已完成任务 ({len(self.completed_tasks)}):")
            for t in self.completed_tasks:
                lines.append(f"  ✓ [{t.task_id}] {t.question[:30]}...")
        
        return "\n".join(lines)

    def reset(self):
        self.queue.clear()
        self.completed_tasks.clear()
        self.task_counter = 0
        self.current_task = None
```

---

## 步骤 2：添加 ResolveTaskTool

**文件**: `src/tools/research_tools.py`

在 FinishTool 之后添加：

```python
class ResolveTaskTool(BaseTool):
    """任务完成工具 - 标记当前子任务已解决"""

    name = "resolve_task"
    description = "标记当前子任务已完成，提供该子任务的答案"
    parameters = {
        "properties": {
            "answer": {"type": "string", "description": "子任务的答案"},
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
```

修改 `create_research_tools()` 函数：

```python
def create_research_tools(kb_manager, web_search) -> List[BaseTool]:
    return [
        KBSearchTool(kb_manager),
        WebSearchTool(web_search, kb_manager),
        DecomposeTool(),
        EvaluateTool(),
        ResolveTaskTool(),  # 新增
        FinishTool()
    ]
```

---

## 步骤 3：集成到 ReActEngine

**文件**: `src/agent/react_engine.py`

### 3.1 导入和初始化

在文件顶部添加导入：
```python
from agent.task_queue import TaskQueue
```

修改 `__init__` 方法（第96-104行）：
```python
def __init__(self, llm_client, tool_registry: ToolRegistry, max_iterations: int = 10):
    self.llm = llm_client
    self.registry = tool_registry
    self.max_iterations = max_iterations
    self.task_queue = TaskQueue()  # 新增
```

### 3.2 run() 方法入口处理

在 `run()` 方法开始处（第122行附近，在创建 trajectory 之后）添加：
```python
trajectory = ResearchTrajectory(question=question)
all_evidences = []

# 新增：初始化任务队列
self.task_queue.reset()
self.task_queue.enqueue(question, parent_id="ROOT", iteration=0)
self.task_queue.dequeue()  # 开始处理根任务
```

### 3.3 工具执行后钩子

在工具执行后（第172行 `result = self.registry.execute(...)` 之后），添加钩子逻辑：

```python
result = self.registry.execute(tool_name, tool_params)

# === 新增：任务队列钩子 ===
# decompose 工具：子问题入队
if tool_name == "decompose" and result.success:
    sub_questions = result.data.get("sub_questions", [])
    parent_id = self.task_queue.current_task.task_id if self.task_queue.current_task else "ROOT"
    for sub_q in sub_questions:
        self.task_queue.enqueue(sub_q, parent_id=parent_id, iteration=iteration)
    print(f"📋 已将 {len(sub_questions)} 个子问题加入队列")

# 搜索工具：证据关联到当前任务
if tool_name in ["kb_search", "web_search"] and result.success:
    new_evidence_ids = result.metadata.get("ids", [])
    if new_evidence_ids:
        self.task_queue.add_evidence_to_current(new_evidence_ids)

# resolve_task 工具：完成当前任务并切换
if tool_name == "resolve_task" and result.success:
    answer = result.data.get("answer", "")
    current_evidence_ids = self.task_queue.current_task.evidence_ids if self.task_queue.current_task else []
    self.task_queue.resolve_current(answer, current_evidence_ids, iteration)
    print(f"✅ 子任务完成，进度: {len(self.task_queue.completed_tasks)}/{len(self.task_queue.completed_tasks) + len(self.task_queue.queue) + (1 if self.task_queue.current_task else 0)}")
    
    # 切换到下一个任务
    if not self.task_queue.is_empty():
        next_task = self.task_queue.dequeue()
        print(f"🔄 切换到: [{next_task.task_id}] {next_task.question}")
# === 钩子结束 ===
```

### 3.4 修改终止条件

修改 finish 工具的终止条件判断（第198-210行）：

```python
# 检查终止条件
if tool_name == "finish" and result.success:
    # 新增：检查是否所有任务完成
    if not self.task_queue.is_all_resolved() and not self.task_queue.is_empty():
        print(f"⚠️ 还有 {len(self.task_queue.queue)} 个任务待处理")
        # 不返回，继续循环
    else:
        answer = result.data.get("answer", "")
        trajectory.final_answer = answer
        trajectory.total_evidences = all_evidences
        
        print(f"\n✅ 研究完成 (轮次: {iteration})")
        return {
            "answer": answer,
            "trajectory": trajectory,
            "iterations": iteration,
            "status": "completed",
            "evidences": all_evidences
        }
```

---

## 步骤 4：增强 Prompt

**文件**: `src/agent/react_engine.py`

### 4.1 修改 REACT_SYSTEM_PROMPT（第52-90行）

替换为：
```python
REACT_SYSTEM_PROMPT = """你是一位资深的研究专家，擅长通过工具调用进行深度研究。

## 可用工具
{tools_prompt}

## 工作流程
你需要通过多轮 Thought-Action-Observation 循环来研究问题：
1. Thought: 分析当前状态，思考下一步应该做什么
2. Action: 选择一个工具并提供参数
3. Observation: 工具执行结果（由系统提供）
4. 重复以上步骤，直到收集足够证据

## 任务分解与队列管理
- 使用 decompose 工具将复杂问题分解为子问题（自动入队）
- 使用 resolve_task 工具标记当前子任务完成（自动切换到下一个）
- 所有子任务完成后，使用 finish 工具生成综合性答案

{queue_status}

## 输出格式
每次回复必须严格遵守以下JSON格式：
```json
{{
  "thought": "你的思考过程，分析当前状态和下一步计划",
  "action": {{
    "tool": "工具名称",
    "params": {{"参数名": "参数值"}}
  }}
}}
```

## 重要规则
1. 每次只能调用一个工具
2. 优先使用 kb_search 搜索本地知识库
3. 如果本地证据不足，使用 web_search 搜索网页
4. 可以使用 decompose 将复杂问题分解为子问题
5. 当前子任务证据充分时，调用 resolve_task 标记完成
6. 所有子任务完成后，调用 finish 工具返回最终答案
7. 答案中必须引用证据编号 [EVD-XXX]

## 当前任务
问题: {question}

{history}

请输出下一步的 thought 和 action（JSON格式）："""
```

### 4.2 修改 Prompt 构建逻辑

修改 run() 方法中的 Prompt 构建部分（第133-137行）：

```python
# 生成队列状态
queue_status = ""
if self.task_queue.current_task or self.task_queue.queue or self.task_queue.completed_tasks:
    queue_status = self.task_queue.get_queue_summary()

prompt = REACT_SYSTEM_PROMPT.format(
    tools_prompt=self.registry.get_tools_prompt(),
    question=question,
    queue_status=queue_status,
    history=trajectory.get_history_prompt()
)
```

---

## 步骤 5：更新 _format_observation

在 `_format_observation` 方法（第255-271行）中添加 resolve_task 的格式化：

```python
def _format_observation(self, result: ToolResult) -> str:
    if not result.success:
        return f"错误: {result.error}"

    data = result.data
    if isinstance(data, dict):
        if "text" in data:
            return data["text"]
        if "answer" in data and data.get("is_final"):  # finish 工具
            return f"最终答案: {data['answer']}"
        if "answer" in data:  # resolve_task 工具
            return f"子任务答案: {data['answer']}"
        if "sub_questions" in data:
            return f"分解为 {len(data['sub_questions'])} 个子问题: {data['sub_questions']}"
        if "assessment" in data:
            return f"评估: {data['assessment']} (充分: {data['is_sufficient']})"

    return str(data)
```

---

## 验证方案

### 测试命令
```bash
cd e:\project\deep_research_agent-main
python main.py
```

### 测试输入
```
/research 银行能否使用客户数据训练大模型？
```

### 预期行为
1. LLM 调用 `decompose` 分解问题
2. 控制台显示 "已将 X 个子问题加入队列"
3. Prompt 中显示队列状态
4. LLM 依次处理每个子任务
5. 每个子任务完成时调用 `resolve_task`
6. 队列清空后 LLM 调用 `finish`

### 成功标准
- [ ] 子问题正确入队（控制台输出确认）
- [ ] 证据正确关联到子任务
- [ ] LLM 理解队列状态并按顺序处理
- [ ] 队列清空后正常触发 finish
