# ReAct 模式深度研究智能体改造

## 目标
将固定7步流程改为 LLM 自主决策的 ReAct 循环

## 实现步骤

### Step 1: 工具基础层
- 新建 `src/tools/base_tool.py` - BaseTool + ToolResult
- 新建 `src/tools/tool_registry.py` - 工具注册中心

### Step 2: 具体工具
- 新建 `src/tools/research_tools.py` - 所有工具实现
  - KBSearchTool, WebSearchTool (封装现有)
  - DecomposeTool, FinishTool (新增)

### Step 3: ReAct 引擎
- 新建 `src/agent/react_engine.py` - 循环引擎 + Prompt + 轨迹

### Step 4: 集成
- 修改 `src/agent/research_agent.py` - 新增 deep_research()
- 修改 `src/main.py` - 路由 /research → deep_research

## 关键文件
- `src/tools/base_tool.py`
- `src/tools/tool_registry.py`
- `src/tools/research_tools.py`
- `src/agent/react_engine.py`
- `src/agent/research_agent.py`
- `src/main.py`

## 验证
```bash
python src/main.py
# 测试: /research 银行能否使用客户数据训练模型？
# 预期: 显示多轮 Thought/Action/Observation
```
