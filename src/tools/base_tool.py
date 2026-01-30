"""工具基础类 - 所有工具的抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def __str__(self):
        if self.success:
            return f"Success: {self.data}"
        return f"Error: {self.error}"


class BaseTool(ABC):
    """工具抽象基类"""

    name: str = ""
    description: str = ""
    parameters: Dict = {}

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def get_spec(self) -> Dict:
        """返回工具规格，供LLM选择"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

    def validate_params(self, params: Dict) -> bool:
        """验证参数"""
        required = self.parameters.get("required", [])
        for key in required:
            if key not in params:
                return False
        return True
