from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.database import async_session_factory
from app.orchestrator.supervisor import dispatch_agent
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2)
def run_agent(self, project_id: str, agent_type: str) -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_session_factory

    async def _run() -> dict:
        async with session_factory() as db:
            await dispatch_agent(project_id, agent_type, db)
            return {"success": True, "project_id": project_id, "agent_type": agent_type}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("Celery task failed: %s", exc)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task
def advance_workflow(project_id: str) -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_session_factory

    async def _run() -> dict:
        from app.orchestrator.supervisor import advance_project

        async with session_factory() as db:
            await advance_project(project_id, db)
            return {"success": True, "project_id": project_id}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("Workflow advance failed: %s", exc)
        return {"success": False, "error": str(exc)}
