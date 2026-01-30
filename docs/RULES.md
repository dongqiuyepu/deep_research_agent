# InfoGatherAgent 开发规范

## 1. 项目元信息

**项目名称:** InfoGatherAgent  
**技术栈:** Python 3.11+, FastAPI, React  
**代码风格:** PEP 8 + Black + Ruff  
**文档更新日期:** 2025-01-30

---

## 2. 依赖管理规范

### 2.1 版本控制

- **开发依赖:** 使用当前最新稳定版本
- **生产依赖:** 锁定具体版本号（使用 `requirements.txt`）
- **API 文档获取:** 通过 [Context7](https://context7.com) 获取最新接口文档

### 2.2 依赖声明

```toml
# pyproject.toml 示例
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"          # 生产环境锁定版本
pydantic = "^2.5.0"
pydantic-settings = "^2.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "*"                   # 开发依赖使用最新版
black = "*"
ruff = "*"
mypy = "*"
```

### 2.3 更新策略

- **每月检查:** 开发依赖更新
- **每季度检查:** 生产依赖更新（需测试验证）
- **安全更新:** 立即响应（使用 `pip-audit` 或 `safety`）

---

## 3. 大模型交互规范

### 3.1 输出格式规范

#### ✅ 强制要求

1. **结构化输出优先**
   - 优先使用 JSON 或 Pydantic 模型定义输出格式
   - 在 Prompt 中明确描述每个字段的含义、类型、约束
   - 禁止使用自由文本作为主要输出格式

2. **推理过程可见**
   - 所有 LLM 输出必须包含独立的 `reason` 字段
   - `reason` 字段必须位于结果数据之前
   - `reason` 用于记录推理过程，不影响业务逻辑

3. **禁止依赖数值性判断**
   - 不依赖 LLM 输出的置信度、正确率、匹配程度等数值
   - 不使用 LLM 生成的评分作为业务逻辑判断依据
   - 如需量化评估，使用规则引擎或专门的评估模型

#### 示例：正确的输出结构

```python
# ✅ 推荐：结构化输出
class QueryGenerationOutput(BaseModel):
    """查询生成输出"""
    reason: str = Field(
        description="生成该查询的推理过程，包括关键词分析、意图识别等"
    )
    queries: List[str] = Field(
        description="生成的搜索查询列表，每个查询应针对不同的信息维度",
        min_length=1,
        max_length=5
    )
    search_strategy: Literal["broad", "specific", "mixed"] = Field(
        description="搜索策略：broad=广泛搜索, specific=精确搜索, mixed=混合"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="附加元数据，如关键词来源、查询类型等"
    )

# ❌ 错误：自由文本 + 数值判断
# {
#   "text": "我生成了3个查询...",
#   "confidence": 0.85,  # ❌ 不可信
#   "quality_score": 92  # ❌ 不可用
# }
```

### 3.2 Prompt 工程规范

#### 结构化 Prompt 模板

```python
STRUCTURED_PROMPT_TEMPLATE = """
你是一个信息搜集助手。请根据以下信息生成搜索查询。

## 输入信息
- 用户关键词: {keywords}
- 上下文记忆: {context}
- 任务目标: {objective}

## 输出要求
请以 JSON 格式输出，包含以下字段：

1. `reason` (string, required): 
   - 描述你的推理过程
   - 说明为什么选择这些查询
   - 分析关键词之间的关联

2. `queries` (array of strings, required):
   - 生成 1-5 个搜索查询
   - 每个查询应覆盖不同维度
   - 查询应简洁明确（10-50字）

3. `search_strategy` (enum, required):
   - "broad": 需要广泛探索时使用
   - "specific": 需要精确答案时使用
   - "mixed": 需要兼顾广度和深度时使用

4. `metadata` (object, optional):
   - 可选的附加信息
   - 如关键词分类、查询类型等

## 示例输出
{{
  "reason": "用户关键词'AI Agent'和'信息搜集'表明需要了解技术实现...",
  "queries": ["AI Agent 架构设计", "信息搜集系统实现"],
  "search_strategy": "specific",
  "metadata": {{"keyword_type": "technical"}}
}}

请严格按照上述 JSON 格式输出，不要包含任何额外的解释文本。
"""
```

### 3.3 响应解析规范

```python
async def parse_llm_response(
    response: str, 
    model: Type[BaseModel]
) -> BaseModel:
    """
    解析 LLM 响应
    
    规则：
    1. 优先使用 Pydantic 验证
    2. 失败时记录原始响应，不静默失败
    3. 提取并记录 reason 字段用于调试
    """
    try:
        # 清理响应（移除 markdown 代码块）
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
            clean_response = clean_response.strip()
        
        # 解析并验证
        parsed = model.model_validate_json(clean_response)
        
        # 记录推理过程
        if hasattr(parsed, 'reason'):
            logger.debug(f"LLM Reasoning: {parsed.reason}")
        
        return parsed
        
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {response}")
        raise LLMResponseParseError(
            f"Invalid response format: {str(e)}"
        ) from e
```

### 3.4 禁止的模式

```python
# ❌ 错误示例 1：依赖数值判断
async def bad_example_1(llm_output: dict):
    if llm_output.get("confidence", 0) > 0.8:  # ❌ 不可靠
        return llm_output["result"]
    return None

# ❌ 错误示例 2：无结构化约束
prompt = "帮我生成一些搜索查询"  # ❌ 输出不可预测

# ❌ 错误示例 3：混合业务数据和推理过程
class BadOutput(BaseModel):
    result: str  # ❌ 推理和结果混在一起
    queries: List[str]

# ✅ 正确示例：分离推理和结果
class GoodOutput(BaseModel):
    reason: str           # ✅ 独立的推理字段
    queries: List[str]    # ✅ 纯业务数据
```

---

## 4. Agent 架构规范

### 4.1 可插拔设计原则

#### 核心要求

1. **组件解耦:** Agent、Tool、Memory 必须可独立替换
2. **接口统一:** 所有同类组件实现相同的抽象接口

#### 实现规范

```python
# agent/core/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, List

class BaseAgent(ABC):
    """Agent 基类 - 所有 Agent 必须继承此类"""
    
    def __init__(
        self,
        name: str,
        llm_provider: "BaseLLMProvider",
        tools: List["BaseTool"],
        memory: Optional["BaseMemory"] = None,
        **kwargs
    ):
        self.name = name
        self.llm = llm_provider
        self.tools = tools
        self.memory = memory
        self._config = kwargs
    
    @abstractmethod
    async def run(self, task: "Task") -> "AgentResult":
        """执行任务（批量模式）"""
        pass
    
    @abstractmethod
    async def stream_run(
        self, 
        task: "Task"
    ) -> AsyncIterator["AgentEvent"]:
        """执行任务（流式模式）"""
        pass
    
    @abstractmethod
    async def plan(self, task: "Task") -> "ExecutionPlan":
        """生成执行计划"""
        pass

# agent/core/base_tool.py
class BaseTool(ABC):
    """工具基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（用于 LLM 理解）"""
        pass
    
    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """参数 JSON Schema"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> "ToolResult":
        """执行工具"""
        pass
```

### 4.2 组件注册机制

```python
# agent/registry.py
from typing import Dict, Type

class ComponentRegistry:
    """组件注册表 - 实现插件化"""
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    _tools: Dict[str, Type[BaseTool]] = {}
    _memories: Dict[str, Type[BaseMemory]] = {}
    
    @classmethod
    def register_agent(cls, name: str):
        """注册 Agent 装饰器"""
        def decorator(agent_class: Type[BaseAgent]):
            cls._agents[name] = agent_class
            return agent_class
        return decorator
    
    @classmethod
    def get_agent(cls, name: str) -> Type[BaseAgent]:
        """获取 Agent 类"""
        if name not in cls._agents:
            raise ValueError(f"Agent '{name}' not registered")
        return cls._agents[name]
    
    # Tool 和 Memory 同理...

# 使用示例
@ComponentRegistry.register_agent("query_generator")
class QueryGeneratorAgent(BaseAgent):
    async def run(self, task: Task) -> AgentResult:
        # 实现...
        pass
```

---

## 5. 代码规范

### 5.1 Python 风格

```python
# 使用 Black 格式化（行长 100）
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py311']

# 使用 Ruff 进行 Linting
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "C4", "DTZ", "T20"]
ignore = ["E501"]  # Black 已处理行长

# 使用 mypy 类型检查
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 5.2 命名规范

```python
# ✅ 文件命名：snake_case
query_generator.py
web_parser.py

# ✅ 类命名：PascalCase
class QueryGeneratorAgent:
    pass

# ✅ 函数/变量：snake_case
async def generate_queries(keywords: List[str]) -> List[str]:
    max_iterations = 10
    
# ✅ 常量：UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# ✅ 私有成员：单下划线前缀
class Agent:
    def _internal_method(self):
        pass
    
    def __private_method(self):  # 名称改写
        pass
```

### 5.3 类型注解

```python
from typing import List, Dict, Optional, Union, Any, Literal
from pydantic import BaseModel

# ✅ 强制要求类型注解
async def fetch_url(
    url: str,
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None
) -> str:
    """Fetch URL content"""
    pass

# ✅ 复杂类型使用 TypeAlias
from typing import TypeAlias

AgentConfig: TypeAlias = Dict[str, Any]
ToolRegistry: TypeAlias = Dict[str, Type[BaseTool]]

# ✅ 使用 Literal 限定字符串枚举
def set_log_level(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None:
    pass
```

### 5.4 异常处理

```python
# utils/exceptions.py
class InfoGatherAgentException(Exception):
    """基础异常类"""
    pass

class LLMResponseParseError(InfoGatherAgentException):
    """LLM 响应解析失败"""
    pass

class ToolExecutionError(InfoGatherAgentException):
    """工具执行失败"""
    pass

class MaxIterationsExceeded(InfoGatherAgentException):
    """超过最大迭代次数"""
    pass

# 使用示例
async def execute_tool(tool: BaseTool, **kwargs):
    try:
        return await tool.execute(**kwargs)
    except Exception as e:
        logger.error(f"Tool {tool.name} failed: {e}")
        raise ToolExecutionError(
            f"Failed to execute {tool.name}: {str(e)}"
        ) from e
```

---

## 6. 测试规范

### 6.1 测试结构

```
tests/
├── unit/                    # 单元测试
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_utils.py
├── integration/             # 集成测试
│   ├── test_agent_pipeline.py
│   └── test_api_endpoints.py
├── e2e/                     # 端到端测试
│   └── test_full_workflow.py
└── conftest.py              # pytest 配置
```

### 6.2 测试覆盖率要求

- **核心模块:** >= 90%
- **工具模块:** >= 80%
- **API 层:** >= 85%
- **总体:** >= 80%

```bash
# 运行测试并生成覆盖率报告
pytest --cov=agent --cov=core --cov-report=html
```

### 6.3 测试示例

```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import AsyncMock, Mock
from agent.agents.query_generator import QueryGeneratorAgent

@pytest.fixture
async def mock_llm():
    """Mock LLM Provider"""
    llm = AsyncMock()
    llm.generate.return_value = """
    {
      "reason": "Test reasoning",
      "queries": ["query 1", "query 2"],
      "search_strategy": "specific"
    }
    """
    return llm

@pytest.mark.asyncio
async def test_query_generator_basic(mock_llm):
    """测试基本查询生成"""
    agent = QueryGeneratorAgent(
        name="test",
        llm_provider=mock_llm,
        tools=[]
    )
    
    task = Task(
        id="test-1",
        keywords=["AI", "Agent"],
        context={},
    )
    
    result = await agent.run(task)
    
    assert len(result.queries) == 2
    assert result.queries[0] == "query 1"
    mock_llm.generate.assert_called_once()
```

---

## 7. 文档规范

### 7.1 代码注释

```python
# ✅ 使用 Google Style Docstring
async def generate_queries(
    keywords: List[str],
    context: Dict[str, Any],
    max_queries: int = 5
) -> List[str]:
    """
    根据关键词和上下文生成搜索查询
    
    Args:
        keywords: 用户提供的关键词列表
        context: 上下文信息，包含用户记忆等
        max_queries: 最大查询数量，默认 5
    
    Returns:
        生成的查询字符串列表
    
    Raises:
        LLMResponseParseError: LLM 响应格式错误
        ValueError: keywords 为空时
    
    Example:
        >>> await generate_queries(["AI", "Agent"], {})
        ["AI Agent architecture", "Agent design patterns"]
    """
    if not keywords:
        raise ValueError("keywords cannot be empty")
    
    # 实现...
```

### 7.2 README 结构

```markdown
# InfoGatherAgent

## 快速开始
## 架构设计
## API 文档
## 开发指南
```

---

## 8. Git 工作流

### 8.1 分支策略

```
main          # 生产环境
  └── dev     # 开发环境
      └── feature/xxx    # 功能分支
      └── bugfix/xxx     # 修复分支
```

### 8.2 Commit 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type):**

- `feat`: 新功能
- `fix`: 修复 Bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链

**示例:**

```
feat(agent): add streaming support for QueryGenerator

- Implement stream_run method
- Add SSE event types
- Update tests

Closes #123
```

---

## 9. 安全规范

### 9.1 敏感信息管理

```python
# ❌ 禁止硬编码
api_key = "sk-xxx"

# ✅ 使用环境变量
from config import settings
api_key = settings.OPENAI_API_KEY.get_secret_value()

# ✅ 日志脱敏
logger.info(f"API Key: {api_key[:10]}***")  # 只显示前缀
```

### 9.2 依赖安全

```bash
# 定期扫描依赖漏洞
pip-audit
safety check

# 在 CI/CD 中集成
# .github/workflows/security.yml
- name: Security Check
  run: |
    pip install safety
    safety check
```

---

## 10. 性能规范

### 10.1 异步优先

```python
# ✅ 使用异步 I/O
async def fetch_multiple_urls(urls: List[str]) -> List[str]:
    tasks = [fetch_url(url) for url in urls]
    return await asyncio.gather(*tasks)

# ❌ 避免同步阻塞
def bad_fetch(urls):
    return [requests.get(url).text for url in urls]  # 串行执行
```

### 10.2 资源限制

```python
# 限制并发数
from asyncio import Semaphore

MAX_CONCURRENT = 10
semaphore = Semaphore(MAX_CONCURRENT)

async def rate_limited_fetch(url: str):
    async with semaphore:
        return await fetch_url(url)
```

---

## 11. 日志规范

### 11.1 日志级别

```python
import logging

# DEBUG: 详细的调试信息
logger.debug(f"LLM prompt: {prompt}")

# INFO: 常规操作记录
logger.info(f"Agent {agent.name} started task {task.id}")

# WARNING: 警告但不影响功能
logger.warning(f"Tool {tool.name} returned empty result")

# ERROR: 错误但程序可继续
logger.error(f"Failed to parse response: {response}")

# CRITICAL: 严重错误，程序可能停止
logger.critical("Database connection lost")
```

### 11.2 结构化日志

```python
# utils/logger.py
import logging
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLoggerAdapter(logging.LoggerAdapter):
    """结构化日志适配器"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """处理日志消息，添加结构化字段"""
        # 从 extra 中提取结构化字段
        extra = kwargs.get("extra", {})
        
        # 构建结构化日志
        log_dict = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": msg,
            **extra
        }
        
        # 将结构化日志转为 JSON 字符串
        kwargs["extra"] = {}  # 清空 extra 避免重复
        return json.dumps(log_dict, ensure_ascii=False), kwargs


def get_logger(name: str) -> StructuredLoggerAdapter:
    """获取结构化日志实例"""
    base_logger = logging.getLogger(name)
    return StructuredLoggerAdapter(base_logger, {})
```

---

## 12. CI/CD 规范

### 12.1 必需的 CI 检查

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Ruff
        run: ruff check .
      
  type-check:
    runs-on: ubuntu-latest
    steps:
      - name: Run mypy
        run: mypy .
  
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest --cov --cov-fail-under=80
  
  security:
    runs-on: ubuntu-latest
    steps:
      - name: Security scan
        run: safety check
```

---
