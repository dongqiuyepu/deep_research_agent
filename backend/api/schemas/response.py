from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    reason: str = Field(..., description="Model reasoning")
    task_id: str
    result: dict = Field(default_factory=dict)
