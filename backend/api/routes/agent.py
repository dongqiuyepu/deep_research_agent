from fastapi import APIRouter

from backend.api.schemas.request import TaskRequest
from backend.api.schemas.response import TaskResponse

router = APIRouter()


@router.post("/agent/run", response_model=TaskResponse)
async def run_agent(payload: TaskRequest) -> TaskResponse:
    return TaskResponse(task_id=payload.task_id, result={}, reason="not_implemented")
