from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models import Project, ProjectAgent
from app.schemas import PaginatedResponse, ProjectCreate, ProjectDetailRead, ProjectRead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(id=str(uuid.uuid4()), name=body.name, description=body.description, status="new", api_config_id=body.api_config_id, erp_config_id=body.erp_config_id)
    db.add(project)
    await db.flush()

    agent_types = ["demand_parser", "solution_generator", "system_config", "data_migration", "ops_qa"]
    for agent_type in agent_types:
        db.add(ProjectAgent(project_id=project.id, agent_type=agent_type, status="pending"))

    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/trigger", response_model=ProjectRead)
async def trigger_workflow(project_id: str, db: AsyncSession = Depends(get_db)):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status not in ("new", "failed"):
        raise HTTPException(status_code=400, detail=f"Project already in progress: {project.status}")

    project.status = "new"
    await db.commit()

    asyncio.create_task(_run_workflow(project.id))
    return project


async def _run_workflow(project_id: str) -> None:
    logger.info("Starting workflow for project %s", project_id)
    from app.database import async_session_factory
    from app.orchestrator.supervisor import advance_project

    async with async_session_factory() as db:
        try:
            await advance_project(project_id, db)
        except Exception as exc:
            logger.exception("Workflow failed for project %s: %s", project_id, exc)


@router.get("", response_model=PaginatedResponse)
async def list_projects(page: int = 1, size: int = 20, status: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Project)
    count_query = select(func.count(Project.id))

    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.order_by(Project.created_at.desc()).offset((page - 1) * size).limit(size))).scalars().all()

    return PaginatedResponse(
        items=[ProjectRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{project_id}", response_model=ProjectDetailRead)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project).options(selectinload(Project.agents)).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Collect generated files + JEECG tenant info BEFORE deletion
    from app.models import Document, ErpConfig
    docs = (await db.execute(select(Document).where(Document.project_id == project_id))).scalars().all()
    files_to_remove = []
    import os, tempfile
    serve_dir = os.path.join(tempfile.gettempdir(), "erp_platform_files")
    for doc in docs:
        if os.path.exists(os.path.join(serve_dir, doc.filename)):
            files_to_remove.append(os.path.join(serve_dir, doc.filename))

    # Get tenant_id: prefer project.tenant_id, fallback to erp_config.tenant_id
    tenant_id = project.tenant_id
    erp_base = None
    if project.erp_config_id:
        ec = (await db.execute(select(ErpConfig).where(ErpConfig.id == project.erp_config_id))).scalar_one_or_none()
        if ec:
            erp_base = ec.base_url
            if not tenant_id:
                tenant_id = ec.tenant_id  # fallback for old projects

    # Delete the project from our DB
    await db.delete(project)
    await db.commit()

    # Clean up generated files
    for f in files_to_remove:
        try: os.remove(f)
        except Exception: pass

    # Clean up JEECG tenant
    if tenant_id and erp_base:
        try:
            import httpx
            # Get admin token
            token_resp = httpx.post(
                f"{erp_base}/sys/login",
                json={"username": "admin", "password": "123456"},
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=10,
            )
            if token_resp.status_code == 200:
                data = token_resp.json()
                token = (data.get("result", {}) or {}).get("token", "")
                if token:
                    # Delete the tenant and all its data
                    resp = httpx.delete(
                        f"{erp_base}/sys/tenant/delete",
                        params={"id": tenant_id},
                        headers={"X-Access-Token": token, "Content-Type": "application/json; charset=utf-8"},
                        timeout=10,
                    )
                    logger.info("JEECG tenant %s cleanup: HTTP %d", tenant_id, resp.status_code)
        except Exception as e:
            logger.warning("JEECG tenant cleanup failed for project %s: %s", project_id, e)
