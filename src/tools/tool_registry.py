"""工具注册中心 - 管理所有可用工具"""

from typing import Dict, List, Optional
from tools.base_tool import BaseTool, ToolResult


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def get_all_specs(self) -> List[Dict]:
        """获取所有工具规格"""
        return [tool.get_spec() for tool in self._tools.values()]

    def get_tools_prompt(self) -> str:
        """生成工具列表的Prompt文本"""
        lines = []
        for tool in self._tools.values():
            params_desc = []
            props = tool.parameters.get("properties", {})
            for k, v in props.items():
                params_desc.append(f"    - {k}: {v.get('description', '')}")
            
            lines.append(f"- {tool.name}: {tool.description}")
            if params_desc:
                lines.append("  参数:")
                lines.extend(params_desc)
        return "\n".join(lines)

    def execute(self, name: str, params: Dict) -> ToolResult:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"未知工具: {name}")
        
        if not tool.validate_params(params):
            return ToolResult(success=False, error=f"参数验证失败: {params}")
        
        try:
            return tool.execute(**params)
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @property
    def tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())
