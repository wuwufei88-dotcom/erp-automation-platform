from __future__ import annotations

from fastapi import APIRouter

from app.api import projects, agents, documents, admin

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(agents.router, prefix="/projects", tags=["agents"])
api_router.include_router(documents.router, prefix="/projects", tags=["documents"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
