from fastapi import FastAPI

from backend.api.routes.agent import router as agent_router
from backend.api.routes.health import router as health_router

app = FastAPI(title="InfoGatherAgent")
app.include_router(health_router)
app.include_router(agent_router)
