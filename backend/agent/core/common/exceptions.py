class AgentFrameworkError(Exception):
    """Base exception for agent framework."""


class MaxIterationsExceeded(AgentFrameworkError):
    """Max iterations exceeded."""
