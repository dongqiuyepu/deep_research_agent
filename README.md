# 行业调研Deep Agent

A structured starter kit for building an AI deep research agent training program. This project uses only the OpenAI library for LLM interaction, allowing trainees to implement custom agent logic from scratch.

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
