class InfoGatherAgentException(Exception):
    """Base exception for InfoGatherAgent."""


class LLMResponseParseError(InfoGatherAgentException):
    """LLM response parse error."""


class ToolExecutionError(InfoGatherAgentException):
    """Tool execution error."""


class MaxIterationsExceeded(InfoGatherAgentException):
    """Max iterations exceeded."""
