from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict

class EventType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    RESULT = "result"


@dataclass
class AgentBaseEvent:
    type: EventType
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime


class AgentThoughtEvent(AgentBaseEvent):
    type = EventType.THOUGHT
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime

class AgentActionEvent(AgentBaseEvent):
    type = EventType.ACTION
    tool_name: str
    tool_args: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime

class AgentResultEvent(AgentBaseEvent):
    type = EventType.RESULT
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
