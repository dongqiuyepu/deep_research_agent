# AI Deep Research Agent - Starter Kit

A structured starter kit for building an AI deep research agent training program. This project uses only the OpenAI library for LLM interaction, allowing trainees to implement custom agent logic from scratch.

## 项目场景: 政策 / 合规 / 监管研究

### 题目一：

「银行是否可以直接使用客户原始交易数据来训练内部大模型？」

目标产出：
• 允许 / 不允许的边界
• 必须满足的前置条件
• 系统侧需要的控制措施

需要检索的数据来源类型：

1️⃣ 上位法与数据保护基本法
• 个人信息保护相关法律条文
关注关键词：
• 个人信息处理的合法性基础
• “目的限定”“最小必要”“另行同意”

2️⃣ 金融监管对客户信息使用的专门规定
• 银行客户信息保密、使用范围限制
• 是否允许“用于模型训练”这种二次用途

3️⃣ 监管或官方解读中的“二次利用”口径
• 是否将“模型训练”视为新的处理目的
• 是否需要重新取得授权/同意

4️⃣ 处罚案例
查找被处罚的情形，例如：
• 未经授权将客户数据用于“分析、建模、画像”
• 超出业务必要范围处理客户数据

这些案例能回答一个关键问题：

监管更看重“是否脱敏”，还是“是否改变用途”？

5️⃣ 行业最佳实践文件
• 银行业或金融科技领域关于：
• 数据脱敏
• 去标识化
• 训练数据隔离区（sandbox）的建议做法

训练要求学员最终给出：
• 是否必须匿名化/去标识化
• 是否必须取得单独同意
• 是否需要建立“训练专用数据域”与生产隔离

⸻

### 题目二：

「基于大模型的自动授信/审批，是否必须保留人工干预？」

目标产出：
• 纯自动决策是否合规
• 在什么情况下必须人工复核
• 系统应如何设计“人工兜底开关”

需要检索的数据来源类型：

1️⃣ 个人自动化决策相关法律条款
重点找：
• 对“自动化决策”的限制
• 是否要求提供拒绝纯自动决策的权利
• 是否要求提供解释与申诉渠道

2️⃣ 金融信贷业务的监管办法
• 授信审批流程是否允许完全自动化
• 是否有“关键决策需人工审核”的要求

3️⃣ 监管问答或政策解读
查找类似问题：
• “算法评分能否直接决定贷款通过/拒绝？”
• 对“人工复核”触发条件的实际口径

4️⃣ 处罚或整改案例
• 因“审批流程过度自动化”被要求整改的银行/机构
• 关注处罚依据引用了哪几条监管规定

5️⃣ 行业规范或白皮书
• 对“人机协同决策”的推荐模式
例如：
• 高风险客户必须人工确认
• 模型只做初筛，人工做终审

训练营交付物应包括：
• 一个可执行规则表，例如：
• 金额 > X 或 风险评分 < Y → 强制人工复核
• 系统架构建议：
• 自动决策模块 + 人工审批工作流 + 审计日志

⸻

### 题目三：

「银行内部使用大模型做客户经理辅助问答，日志要保存多久、谁可以查看？」

目标产出：
• 日志留存期限
• 访问权限与审计要求
• 是否涉及客户隐私与最小化存储

需要检索的数据来源类型：

1️⃣ 金融信息系统运行与安全管理类监管规定
重点找：
• 日志留存最低期限要求
• 安全审计、可追溯性要求

2️⃣ 数据安全与个人信息保护相关规定
• 是否允许长期保存包含客户信息的对话日志
• 是否要求脱敏或分级存储

3️⃣ 监管检查/审计指引
• 检查时通常要求调取哪些日志
• 对“可追溯到个人操作”的要求

4️⃣ 处罚案例
• 因日志缺失、不可追溯被处罚的案例
• 因内部人员越权查看客户信息被处罚的案例

5️⃣ 行业实践指南
• 推荐的做法通常包括：
• 日志分级保存（操作日志 vs 内容日志）
• 敏感字段脱敏
• 严格的访问审批与留痕

训练营期望学员给出：
• 明确的策略，例如：
• 操作审计日志 ≥ N 年
• 含客户内容的对话日志：脱敏后保存 M 年
• 权限模型：
• 默认仅安全/审计角色可查看原始日志
• 业务人员只能看聚合或脱敏版本

⸻

训练重点不在“找到一个答案”，而在“建立证据链”

学员必须做到： 1. 每条结论都能追溯到
• 法规条文 或
• 监管文件编号 或
• 具体处罚决定书 2. 区分三类证据权重：
• 强制性要求（必须做）
• 审慎性建议（最好做）
• 行业常见做法（可以参考） 3. 当不同来源冲突时：
• 以上位法与处罚案例优先
• 解读与白皮书只能作为辅助说明

通过这样的具体问题 + 分层数据源，你的 Deep Research Agent 训练就会逼着学员完成三件事：

找全 → 对齐 → 归纳为可落地的系统与流程规则

## Features

- Simple command-line chat interface
- Direct OpenAI API integration (no frameworks)
- Modular architecture with separate concerns
- Environment-based configuration
- Conversation history management

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your API credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

**Note:** If you're using a different OpenAI-compatible API, update the `OPENAI_BASE_URL` accordingly.

### 3. Run the Application

```bash
cd src
python main.py
```

## Usage

Once running, you can chat with the AI assistant:

```text
You: Hello!
Assistant: Hi! How can I help you today?

You: Tell me about AI agents
Assistant: [Response about AI agents...]
```

Type `quit` or `exit` to end the conversation.

## Project Structure

```text
deep_research_agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main chat loop
│   ├── llm.py               # LLM client wrapper
│   ├── agent/               # Agent logic and reasoning
│   │   ├── __init__.py
│   │   └── README.md
│   ├── memory/              # Conversation memory & context
│   │   ├── __init__.py
│   │   └── README.md
│   ├── knowledge_base/      # Document storage & retrieval
│   │   ├── __init__.py
│   │   └── README.md
│   └── tools/               # External tools & integrations
│       ├── __init__.py
│       └── README.md
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment configuration
├── .env                    # Your actual environment variables (gitignored)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Module Overview

### `src/llm.py`

LLM client wrapper that handles OpenAI API communication. Trainees can extend this to add streaming, function calling, or different model configurations.

### `src/agent/`

Core agent logic including reasoning patterns (ReAct, Chain of Thought), task planning, and tool orchestration. This is where the "intelligence" of the research agent lives.

### `src/memory/`

Memory management for conversation history, context window handling, summarization, and potentially vector-based semantic memory.

### `src/knowledge_base/`

Document storage and retrieval system. Implement RAG (Retrieval Augmented Generation), vector databases, and source tracking here.

### `src/tools/`

External tools the agent can use: web search, web scraping, calculators, code execution, file operations, etc.

## Training Exercises

This starter kit provides a foundation for trainees to build upon. Suggested exercises:

1. **Memory Module** - Implement conversation history storage and retrieval
2. **Tool System** - Create a web search tool with API integration
3. **Agent Logic** - Implement ReAct pattern for reasoning and acting
4. **Knowledge Base** - Build a simple RAG system with vector search
5. **Multi-step Research** - Chain multiple tools together for complex queries
6. **Source Tracking** - Add citation and source management
7. **Streaming Responses** - Implement streaming for better UX

## Notes

- The chat maintains conversation history in memory (resets on restart)
- Uses `gpt-4o-mini` by default (can be changed in `src/llm.py`)
- No agent frameworks are used - all logic is explicit and customizable
- Each module has its own README with implementation suggestions
- Error handling is basic - enhance as needed for production use

## License

This is a training starter kit - use and modify as needed for educational purposes.
