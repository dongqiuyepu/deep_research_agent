# -*- coding: utf-8 -*-
"""Test rebuild functionality"""

from knowledge_base import KnowledgeBaseManager
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))


def test_rebuild():
    """Test /rebuild command"""
    print("=" * 60)
    print("Testing /rebuild command")
    print("=" * 60)

    current_dir = Path(__file__).parent.parent
    doc_dir = str(current_dir / "data" / "documents")
    chroma_dir = str(current_dir / "data" / "chroma_db")

    print(f"Doc dir: {doc_dir}")
    print(f"Chroma dir: {chroma_dir}")

    kb_manager = KnowledgeBaseManager(persist_dir=chroma_dir)

    print("\n[Step 1] Rebuilding index...")
    result = kb_manager.rebuild_index(doc_dir)

    if result:
        print("\n[OK] Index rebuilt successfully!")

        # Test query
        print("\n[Step 2] Testing query...")
        evidences, text = kb_manager.search("test query", top_k=3)
        print(f"Found {len(evidences)} evidences")

        return True
    else:
        print("\n[FAIL] Index rebuild failed!")
        return False


if __name__ == "__main__":
    success = test_rebuild()
    sys.exit(0 if success else 1)
