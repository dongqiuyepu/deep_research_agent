from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    task_id: str = Field(..., description="Task id")
    keywords: list[str] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    requirements: str | None = None
