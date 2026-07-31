from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.registry import get_agent
from app.api.ws import notify_agent_state
from app.models import AgentExecution, AgentLog, Project, ProjectAgent
from app.orchestrator.state_machine import AGENT_FOR_STATE, ProjectState, next_state

logger = logging.getLogger(__name__)


async def advance_project(project_id: str, db: AsyncSession) -> None:
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        return

    current = ProjectState(project.status)

    target_state = next_state(current)
    if target_state is None:
        return

    agent_type = AGENT_FOR_STATE.get(target_state)
    if not agent_type:
        project.status = target_state.value
        await db.commit()
        return

    await dispatch_agent(project_id, agent_type, db)


async def dispatch_agent(project_id: str, agent_type: str, db: AsyncSession) -> None:
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        return

    agent_record = (
        await db.execute(
            select(ProjectAgent).where(
                ProjectAgent.project_id == project_id,
                ProjectAgent.agent_type == agent_type,
            )
        )
    ).scalar_one_or_none()

    if not agent_record:
        return

    target_state = ProjectState(project.status)
    if target_state == ProjectState.NEW:
        target_state = ProjectState.DEMAND_PARSE
    else:
        target_state = next_state(target_state)
        if target_state is None:
            return

    agent_record.status = "running"
    agent_record.started_at = datetime.now(timezone.utc)
    project.status = target_state.value
    notify_agent_state(project_id, agent_type, "running", f"Agent started")

    execution = AgentExecution(
        project_agent_id=agent_record.id,
        attempt_number=agent_record.retry_count + 1,
        status="running",
    )
    db.add(execution)
    await db.commit()

    try:
        previous_outputs = await _collect_previous_outputs(project_id, agent_type, db)
        documents = await _collect_documents(project_id, db)

        context = AgentContext(
            project_id=project_id,
            agent_type=agent_type,
            previous_outputs=previous_outputs,
            documents=documents,
            api_config=await _get_api_config(project, db),
            erp_config=await _get_erp_config(project, db),
        )

        agent = get_agent(agent_type)
        if agent is None:
            raise RuntimeError(f"Agent {agent_type} not found in registry")

        result = await agent.execute(context)

        if result.success:
            agent_record.status = "completed"
            agent_record.result_json = result.output
            execution.status = "completed"
            project.status = target_state.value
            notify_agent_state(project_id, agent_type, "completed", "Agent completed successfully")

            # Cache agent output in Redis
            from app.cache import agent_output_key, cache_set
            await cache_set(agent_output_key(project_id, agent_type), result.output, ttl=604800)  # 7 days
        else:
            agent_record.status = "failed"
            agent_record.error_message = result.error
            execution.status = "failed"
            project.status = ProjectState.FAILED.value
            notify_agent_state(project_id, agent_type, "failed", result.error or "Unknown error")

    except Exception as exc:
        logger.exception("Agent %s failed for project %s", agent_type, project_id)
        agent_record.status = "failed"
        agent_record.error_message = str(exc)
        execution.status = "failed"
        project.status = ProjectState.FAILED.value
        notify_agent_state(project_id, agent_type, "failed", str(exc))

        db.add(
            AgentLog(
                execution_id=execution.id,
                level="error",
                message=f"Agent execution failed: {exc}",
            )
        )

    execution.completed_at = datetime.now(timezone.utc)
    agent_record.completed_at = datetime.now(timezone.utc)

    if agent_record.status == "completed":
        await db.commit()
        next_target = next_state(ProjectState(project.status))
        if next_target is not None:
            await advance_project(project_id, db)
    else:
        await db.commit()


async def _collect_previous_outputs(project_id: str, current_agent: str, db: AsyncSession) -> dict:
    all_agents = (
        await db.execute(
            select(ProjectAgent).where(
                ProjectAgent.project_id == project_id,
                ProjectAgent.agent_type != current_agent,
                ProjectAgent.status == "completed",
            )
        )
    ).scalars().all()

    outputs: dict[str, dict] = {}
    for agent in all_agents:
        if agent.result_json:
            outputs[agent.agent_type] = agent.result_json
    return outputs


async def _collect_documents(project_id: str, db: AsyncSession) -> list[str]:
    from app.models import Document

    docs = (
        await db.execute(
            select(Document.minio_key).where(
                Document.project_id == project_id,
                Document.doc_type == "requirement",
            )
        )
    ).scalars().all()
    return list(docs)


async def _get_erp_config(project: Project, db: AsyncSession) -> dict | None:
    if not project.erp_config_id:
        return None
    from app.models import ErpConfig
    config = (await db.execute(select(ErpConfig).where(ErpConfig.id == project.erp_config_id))).scalar_one_or_none()
    if not config:
        return None
    return {
        "provider": config.provider,
        "base_url": config.base_url,
        "auth_type": config.auth_type,
        "token_url": config.token_url,
        "token_header": config.token_header,
        "credential_key": config.credential_key,
        "credential_secret": config.credential_secret,
        "static_token": config.static_token,
        "tenant_id": config.tenant_id,
    }


async def _get_api_config(project: Project, db: AsyncSession) -> dict | None:
    if not project.api_config_id:
        return None
    from app.models import ApiConfig
    config = (await db.execute(select(ApiConfig).where(ApiConfig.id == project.api_config_id))).scalar_one_or_none()
    if not config:
        return None
    return {"base_url": config.base_url, "api_key": config.api_key, "model_name": config.model_name, "provider": config.provider}
