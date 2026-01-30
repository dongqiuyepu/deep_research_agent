# -*- coding: utf-8 -*-
"""Test script for Deep Research Agent"""

from agent import ResearchAgent
from memory import ConversationMemory
from tools import WebSearchTool
from knowledge_base import KnowledgeBaseManager
from llm import LLMClient
import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_system():
    """Test system components"""
    print("=" * 60)
    print("Deep Research Agent - System Test")
    print("=" * 60)

    # 1. Test LLM
    print("\n[1/5] Testing LLM connection...")
    try:
        llm = LLMClient()
        response = llm.chat(
            [{"role": "user", "content": "Hello, reply in one sentence"}])
        print(f"  [OK] LLM response: {response[:50]}...")
    except Exception as e:
        print(f"  [FAIL] LLM test failed: {e}")
        return False

    # 2. Test knowledge base
    print("\n[2/5] Testing knowledge base...")
    current_dir = Path(__file__).parent.parent
    doc_dir = str(current_dir / "data" / "documents")
    chroma_dir = str(current_dir / "data" / "chroma_db")

    try:
        kb_manager = KnowledgeBaseManager(persist_dir=chroma_dir)
        kb_manager.initialize(doc_dir)
        print(f"  [OK] Knowledge base initialized")
        print(f"    Doc dir: {doc_dir}")
    except Exception as e:
        print(f"  [FAIL] Knowledge base test failed: {e}")
        return False

    # 3. Test web search
    print("\n[3/5] Testing web search...")
    try:
        web_search = WebSearchTool()
        if web_search.is_available():
            results = web_search.search(
                "data protection law banking", max_results=2)
            print(f"  [OK] Web search returned {len(results)} results")
            if results:
                print(f"    Example: {results[0].title[:40]}...")
        else:
            print("  [WARN] Web search not available (check TAVILY_API_KEY)")
    except Exception as e:
        print(f"  [FAIL] Web search test failed: {e}")

    # 4. Test memory
    print("\n[4/5] Testing conversation memory...")
    try:
        memory = ConversationMemory()
        memory.add_user_message("test message")
        memory.add_assistant_message("test reply")
        history = memory.get_history()
        print(f"  [OK] Memory working, {len(history)} messages stored")
    except Exception as e:
        print(f"  [FAIL] Memory test failed: {e}")
        return False

    # 5. Test full research flow
    print("\n[5/5] Testing full research flow...")
    try:
        agent = ResearchAgent(
            llm_client=llm,
            kb_manager=kb_manager,
            web_search=web_search,
            memory=ConversationMemory()
        )

        test_question = "Can banks use customer data to train AI models?"
        print(f"  Test question: {test_question}")

        result = agent.research(
            question=test_question,
            use_web_search=web_search.is_available(),
            top_k=3
        )

        print("\n" + "=" * 60)
        print("Test Result:")
        print("=" * 60)
        print(result["formatted_response"][:1500])
        if len(result["formatted_response"]) > 1500:
            print("...(truncated)")

        print("\n" + "=" * 60)
        print("[OK] System test passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"  [FAIL] Research flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)
