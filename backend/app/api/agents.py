from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import AgentExecution, AgentLog, ProjectAgent
from app.schemas import AgentExecutionRead, AgentLogRead, AgentRead

router = APIRouter()


@router.get("/{project_id}/agents", response_model=list[AgentRead])
async def list_project_agents(project_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ProjectAgent).where(ProjectAgent.project_id == project_id))).scalars().all()
    return [AgentRead.model_validate(r) for r in rows]


@router.get("/{project_id}/agents/{agent_type}", response_model=AgentRead)
async def get_project_agent(project_id: str, agent_type: str, db: AsyncSession = Depends(get_db)):
    agent = (
        await db.execute(
            select(ProjectAgent).where(
                ProjectAgent.project_id == project_id,
                ProjectAgent.agent_type == agent_type,
            )
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{project_id}/agents/{agent_type}/output")
async def get_agent_output(project_id: str, agent_type: str, db: AsyncSession = Depends(get_db)):
    # Try Redis cache first
    from app.cache import agent_output_key, cache_get
    cached = await cache_get(agent_output_key(project_id, agent_type))
    if cached:
        return cached

    agent = (
        await db.execute(
            select(ProjectAgent).where(
                ProjectAgent.project_id == project_id,
                ProjectAgent.agent_type == agent_type,
            )
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not agent.result_json:
        raise HTTPException(status_code=404, detail="No output available")
    return agent.result_json


@router.get("/{project_id}/agents/{agent_type}/executions", response_model=list[AgentExecutionRead])
async def list_agent_executions(project_id: str, agent_type: str, db: AsyncSession = Depends(get_db)):
    agent = (
        await db.execute(
            select(ProjectAgent).where(
                ProjectAgent.project_id == project_id,
                ProjectAgent.agent_type == agent_type,
            )
        )
    ).scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    executions = (
        await db.execute(
            select(AgentExecution)
            .where(AgentExecution.project_agent_id == agent.id)
            .order_by(AgentExecution.started_at.desc())
        )
    ).scalars().all()
    return [AgentExecutionRead.model_validate(e) for e in executions]


@router.get("/{project_id}/executions/{execution_id}/logs", response_model=list[AgentLogRead])
async def get_execution_logs(project_id: str, execution_id: str, db: AsyncSession = Depends(get_db)):
    logs = (
        await db.execute(
            select(AgentLog).where(AgentLog.execution_id == execution_id).order_by(AgentLog.created_at.asc())
        )
    ).scalars().all()
    return [AgentLogRead.model_validate(log) for log in logs]
