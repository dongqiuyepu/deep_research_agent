"""对话记忆 - 简单的对话历史管理"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Message:
    """消息数据结构"""
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}


class ConversationMemory:
    """对话记忆管理"""

    def __init__(self, max_history: int = 20):
        """
        初始化对话记忆

        Args:
            max_history: 最大保留的消息数量
        """
        self.messages: List[Message] = []
        self.max_history = max_history

    def add_message(self, role: str, content: str) -> Message:
        """
        添加消息

        Args:
            role: 角色 ("user" 或 "assistant")
            content: 消息内容

        Returns:
            Message 对象
        """
        message = Message(role=role, content=content)
        self.messages.append(message)

        # 保持历史记录在限制范围内
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

        return message

    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        return self.add_message("user", content)

    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content)

    def get_history(self) -> List[Dict[str, str]]:
        """
        获取完整对话历史

        Returns:
            消息字典列表，适用于 OpenAI API 格式
        """
        return [msg.to_dict() for msg in self.messages]

    def get_recent(self, n: int = 5) -> List[Dict[str, str]]:
        """
        获取最近 n 条消息

        Args:
            n: 消息数量

        Returns:
            消息字典列表
        """
        recent = self.messages[-n:] if len(
            self.messages) >= n else self.messages
        return [msg.to_dict() for msg in recent]

    def get_context_string(self, n: int = 5) -> str:
        """
        获取最近对话的字符串形式

        Args:
            n: 消息数量

        Returns:
            格式化的对话字符串
        """
        recent = self.messages[-n:] if len(
            self.messages) >= n else self.messages

        lines = []
        for msg in recent:
            role_label = "用户" if msg.role == "user" else "助手"
            lines.append(f"{role_label}: {msg.content}")

        return "\n".join(lines)

    def clear(self):
        """清空对话历史"""
        self.messages.clear()

    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """获取最后一条助手消息"""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.content
        return None

    def __len__(self) -> int:
        return len(self.messages)
