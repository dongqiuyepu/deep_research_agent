from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class ToolResult:
    output: Dict[str, Any]


@dataclass
class AgentResult:
    output: Dict[str, Any]
