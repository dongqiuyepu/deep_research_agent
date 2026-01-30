# Deep Research Agent 灵活智能体架构改造计划

## 目标

将现有的固定7步研究流程改造为 **ReAct 模式驱动的自主决策系统**，让 LLM 能够：
- 自主决定下一步行动（搜索、分析、总结）
- 多轮迭代直到收集足够证据
- 分解复杂问题为子问题
- 混合终止（LLM判断 + 最大轮次保护）

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│                    主入口 (main.py)                  │
│  /research → 深度研究    │  默认 → 普通对话         │
└──────────────┬──────────────────────────────────────┘
               │
   ┌───────────┴───────────┐
   │                       │
   ▼                       ▼
┌───────────────┐  ┌────────────────────────┐
│ simple_chat() │  │   deep_research()      │
│   [不变]      │  │   [ReAct循环引擎]      │
└───────────────┘  └──────────┬─────────────┘
                              │
                   ┌──────────┴──────────┐
                   │  ReActResearchEngine │
                   │  - Thought (思考)    │
                   │  - Action (选择工具) │
                   │  - Observation (观察)│
                   │  - 终止检测          │
                   └──────────┬───────────┘
                              │
                   ┌──────────┴──────────┐
                   │    ToolRegistry      │
                   │   (工具注册中心)      │
                   └──────────┬───────────┘
                              │
      ┌───────────────────────┼───────────────────────┐
      │                       │                       │
      ▼                       ▼                       ▼
┌─────────────┐      ┌─────────────────┐      ┌──────────────┐
│ 搜索类工具   │      │   分析类工具     │      │ 生成类工具    │
│- kb_search  │      │- decompose      │      │- synthesize  │
│- web_search │      │- evaluate       │      │- finish      │
└─────────────┘      └─────────────────┘      └──────────────┘
```

## ReAct 循环流程

```
用户问题
    ↓
┌─────────────────────────────────────┐
│ 构建 ReAct Prompt                    │
│ - 系统指令 + 可用工具 + 历史轨迹     │
└─────────────┬───────────────────────┘
              │
              ▼ (循环开始)
┌─────────────────────────────────────┐
│ 1. LLM Thought: 分析当前状态         │
│ 2. LLM Action: 选择工具+参数         │
│ 3. 执行工具，获取 Observation        │
│ 4. 记录到历史轨迹                    │
│ 5. 检查终止条件                      │
│    - LLM调用finish工具? → 结束       │
│    - 达到max_iterations? → 强制结束  │
│    - 否则 → 继续循环                 │
└─────────────────────────────────────┘
              ↓
         生成最终报告
```

## 新增文件

### 工具系统
| 文件 | 描述 |
|------|------|
| `src/tools/base_tool.py` | BaseTool 抽象基类 + ToolResult 数据类 |
| `src/tools/tool_registry.py` | 工具注册中心，管理所有工具 |
| `src/tools/search_tools.py` | 搜索类工具（kb_search, web_search） |
| `src/tools/analyze_tools.py` | 分析类工具（decompose, evaluate） |
| `src/tools/generate_tools.py` | 生成类工具（synthesize, finish） |

### ReAct 引擎
| 文件 | 描述 |
|------|------|
| `src/agent/react_engine.py` | ReAct 循环执行引擎 |
| `src/agent/react_prompt.py` | ReAct 专用 Prompt 构建 |
| `src/agent/trajectory.py` | 研究轨迹记录 |

## 修改文件

| 文件 | 改动 |
|------|------|
| `src/agent/research_agent.py` | 新增 `deep_research()` 方法，保留 `legacy_research()` |
| `src/main.py` | 更新命令路由，`/research` 调用新 ReAct 模式 |
| `src/tools/__init__.py` | 导出新工具类 |

## 工具定义

### 搜索类
- **kb_search**: 知识库向量检索
- **web_search**: 网页搜索

### 分析类
- **decompose**: 将复杂问题分解为子问题
- **evaluate**: 评估证据质量和相关性

### 生成类
- **synthesize**: 从多个子答案合成最终答案
- **finish**: 标记研究完成，返回最终结果

## 终止条件

1. **LLM主动结束**: 调用 `finish` 工具
2. **最大轮次**: 默认 10 轮
3. **连续错误**: 连续 3 次工具调用失败

## 实现步骤

### Step 1: 工具系统基础
1. 实现 `BaseTool` 抽象类和 `ToolResult` 数据类
2. 实现 `ToolRegistry` 工具注册中心
3. 封装现有知识库和网页搜索为工具

### Step 2: ReAct 引擎
1. 实现 `Trajectory` 轨迹记录类
2. 实现 ReAct Prompt 构建器
3. 实现 `ReActResearchEngine` 循环引擎
4. 实现 LLM 输出 JSON 解析

### Step 3: 分析和生成工具
1. 实现 `DecomposeTool` 子问题分解
2. 实现 `EvaluateTool` 证据评估
3. 实现 `SynthesizeTool` 答案合成
4. 实现 `FinishTool` 完成标记

### Step 4: 集成
1. 在 `ResearchAgent` 中集成 ReAct 引擎
2. 更新 `main.py` 命令路由
3. 保持普通对话模式不变

### Step 5: 测试验证
1. 单元测试各工具
2. 端到端测试 ReAct 流程
3. 对比新旧模式效果

## 关键实现细节

### BaseTool 抽象基类设计
```python
# src/tools/base_tool.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class ToolResult:
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict = None

class BaseTool(ABC):
    name: str           # 工具唯一标识
    description: str    # 工具描述（供LLM理解）
    parameters: Dict    # 参数Schema
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass
    
    def get_spec(self) -> Dict:
        """返回工具规格，供LLM选择"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
```

### ReAct Prompt 模板
```
你是一位资深研究专家，通过工具调用进行深度研究。

可用工具：
{tools_json}

每次输出必须是JSON格式：
{
  "thought": "你的思考过程",
  "action": {
    "tool": "工具名称",
    "params": {"参数名": "参数值"}
  }
}

当你认为证据足够时，调用 finish 工具返回最终答案。
```

### 输出展示格式（详细模式）
```
[轮次 1/10]
💭 Thought: 需要先从知识库查找相关政策...
🔧 Action: kb_search(query="银行 客户数据 模型训练")
📋 Observation: 找到3条证据 [EVD-001, EVD-002, EVD-003]

[轮次 2/10]
💭 Thought: 知识库证据不够，需要网页搜索...
🔧 Action: web_search(query="银行大模型监管政策2024")
📋 Observation: 找到2条网页证据 [EVD-004, EVD-005]

[轮次 3/10]
💭 Thought: 证据足够，可以生成答案
🔧 Action: finish(answer="...")
✅ 研究完成
```

## 验证方式

1. 运行 `python src/main.py`
2. 测试普通对话：直接输入问题（应保持原有行为）
3. 测试深度研究：`/research 银行是否可以使用客户数据训练模型？`
4. 验证输出：
   - 每轮显示 Thought/Action/Observation
   - 证据ID正确递增（EVD-001, EVD-002...）
   - LLM能自主决定何时结束
5. 验证终止条件：
   - 正常情况：LLM调用 finish 工具
   - 异常情况：达到 max_iterations(10) 强制结束
6. 验证旧版兼容：`/research_v1` 应调用原有固定流程
