# InfoGatherAgent 项目结构

## 1. 项目概述

基于 FastAPI 的 Agentic 信息搜集系统。系统通过用户提供的关键字和记忆信息智能生成搜索查询，执行信息采集任务，并生成结构化报告。核心特性包括自主实现的 Agent 框架、流式响应能力和混合编排架构。

**核心能力：**

- 智能查询生成与优化
- 多源信息采集与解析
- 实时流式反馈
- 上下文记忆管理
- 报告自动生成

## 2. 技术栈

| 层级       | 技术选型           | 说明               |
| ---------- | ------------------ | ------------------ |
| 后端语言   | Python 3.11+       | 异步编程支持       |
| Web 框架   | FastAPI            | 原生异步、SSE 支持 |
| AI 框架    | 自主实现           | 轻量级、可定制     |
| 前端框架   | React              | 组件化开发         |
| 通信协议   | Server-Sent Events | 单向流式推送       |
| LLM 提供商 | OpenAI/Anthropic   | 可配置多提供商     |

## 3. 项目结构

```
info_gather_agent/
├── agent/                          # Agent 核心模块
│   ├── core/                       # Agent 基础框架
│   │   ├── __init__.py
│   │   ├── base.py        # Agent 基类定义
│   │   ├── run.py         # Agent 执行引擎
│   │   ├── tool.py        # 工具注册与管理
│   │   └── context.py     # 上下文管理器
│   ├── agents/                     # 具体 Agent 实现
│   │   ├── __init__.py
│   │   ├── query_generator.py     # 查询生成 Agent
│   │   ├── info_gatherer.py       # 信息采集 Agent
│   │   └── report_writer.py       # 报告生成 Agent
│   ├── tools/                      # Agent 可用工具
│   │   ├── __init__.py
│   │   ├── search_tool.py         # 搜索工具
│   │   ├── fetch_tool.py          # 网页抓取工具
│   │   └── parse_tool.py          # 内容解析工具
│   └── memory/                     # 记忆系统
│       ├── __init__.py
│       ├── short_term.py          # 短期记忆（会话级）
│       └── long_term.py           # 长期记忆（持久化）
│
├── pipeline/                       # Pipeline 模块（非 Agent 流程）
│   ├── __init__.py
│   ├── web_parser.py              # 网页解析管道
│   ├── content_cleaner.py         # 内容清洗管道
│   └── data_validator.py          # 数据验证管道
│
├── core/                           # 业务核心逻辑
│   ├── __init__.py
│   ├── orchestrator.py            # 编排器（统一入口）
│   ├── task_manager.py            # 任务管理
│   └── result_aggregator.py       # 结果聚合
│
├── provider/                       # 外部服务提供者
│   ├── __init__.py
│   ├── llm/                       # LLM 提供者
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   └── anthropic_provider.py
│   ├── search/                    # 搜索服务
│   │   ├── base.py
│   │   └── serper_provider.py
│   └── storage/                   # 存储服务
│       ├── base.py
│       └── local_storage.py
│
├── api/                            # API 层
│   ├── __init__.py
│   ├── routes/                    # 路由定义
│   │   ├── agent.py              # Agent 相关接口
│   │   └── health.py             # 健康检查
│   ├── schemas/                   # Pydantic 数据模型
│   │   ├── request.py
│   │   └── response.py
│   └── dependencies.py            # 依赖注入
│
├── utils/                          # 工具模块
│   ├── __init__.py
│   ├── logger.py                  # 日志配置
│   ├── config.py                  # 配置管理
│   └── exceptions.py              # 自定义异常
│
├── tests/                          # 测试目录
│   ├── unit/
│   └── integration/
│
├── .env.example                   # 环境变量示例
├── .env                           # 环境变量（不提交）
├── pyproject.toml                 # 项目配置
└── main.py                        # 应用入口
```

## 4. 核心模块说明

### 4.1 Agent Core

**职责：** 提供 Agent 运行的基础框架

**核心组件：**

```python
# agent/core/base_agent.py
class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, llm_provider, tools: List[Tool]):
        self.name = name
        self.llm = llm_provider
        self.tools = tools
        self.context = ContextManager()
    
    @abstractmethod
    async def run(self, task: Task) -> AgentResult:
        """执行 Agent 任务"""
        pass
    
    async def stream_run(self, task: Task) -> AsyncIterator[Event]:
        """流式执行（用于 SSE）"""
        pass
```

### 4.2 Orchestrator

**职责：** 协调 Agent 和 Pipeline 的执行流程

**设计模式：** 混合编排模式

```python
# core/orchestrator.py
class Orchestrator:
    """
    支持三种执行模式：
    1. Pure Agent：完全由 Agent 决策
    2. Pure Pipeline：固定流程执行
    3. Hybrid：Agent 调用 Pipeline 作为工具
    """
    
    async def execute(self, mode: str, task: Task) -> Result:
        if mode == "agent":
            return await self._agent_mode(task)
        elif mode == "pipeline":
            return await self._pipeline_mode(task)
        else:
            return await self._hybrid_mode(task)
```

### 4.3 Provider Layer

**职责：** 抽象外部服务依赖，便于切换和测试

```python
# provider/llm/base.py
class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        pass
```

## 5. 关键数据结构

### 5.1 Task（任务）

```python
@dataclass
class Task:
    id: str
    keywords: List[str]
    context: Dict[str, Any]  # 用户提供的记忆信息
    requirements: Optional[str]
    created_at: datetime
```

### 5.2 AgentEvent（流式事件）

```python
class EventType(Enum):
    THOUGHT = "thought"      # Agent 思考过程
    ACTION = "action"        # 执行的动作
    OBSERVATION = "observation"  # 观察结果
    RESULT = "result"        # 最终结果

@dataclass
class AgentEvent:
    type: EventType
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
```

### 5.3 Tool（工具）

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    executor: Callable
```

## 6. 关键函数（简述）

### 6.1 Agent 执行流程

```python
async def agent_run_loop(agent: BaseAgent, task: Task):
    """
    ReAct 模式执行循环：
    1. Thought：分析当前状态
    2. Action：选择并执行工具
    3. Observation：获取执行结果
    4. 重复直到任务完成
    """
    pass
```

### 6.2 SSE 流式推送

```python
async def stream_agent_events(task_id: str) -> AsyncIterator[str]:
    """
    将 Agent 执行过程通过 SSE 推送给前端
    事件格式：data: {"type": "thought", "content": "..."}
    """
    pass
```

### 6.3 记忆管理

```python
async def update_memory(user_id: str, info: Dict):
    """更新用户长期记忆"""
    pass

async def retrieve_context(user_id: str, keywords: List[str]) -> Dict:
    """基于关键字检索相关记忆"""
    pass
```

## 7. 环境变量管理

```python
# .env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

