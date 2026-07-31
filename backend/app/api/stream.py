# SSE streaming endpoint for real-time agent execution
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.llm import build_json_schema
from app.agents.registry import get_agent
from app.agents.stream import agent_loop_stream
from app.api.deps import get_db
from app.models import Project, ProjectAgent
from app.tools.registry import execute_tool, get_tool_definitions

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/projects/{project_id}/agents/{agent_type}/stream")
async def stream_agent(project_id: str, agent_type: str, request: Request, db: AsyncSession = Depends(get_db)):
    """SSE endpoint that streams agent execution in real-time."""
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    agent_record = (await db.execute(
        select(ProjectAgent).where(ProjectAgent.project_id == project_id, ProjectAgent.agent_type == agent_type)
    )).scalar_one_or_none()
    if not agent_record:
        raise HTTPException(404, "Agent not found")

    agent = get_agent(agent_type)
    if not agent:
        raise HTTPException(404, f"Agent {agent_type} not registered")

    # Gather context
    from app.orchestrator.supervisor import _collect_previous_outputs, _collect_documents, _get_api_config, _get_erp_config

    async def _load_context():
        async with db as session:
            prev = await _collect_previous_outputs(project_id, agent_type, session)
            docs = await _collect_documents(project_id, session)
            api_cfg = await _get_api_config(project, session)
            erp_cfg = await _get_erp_config(project, session)
            return AgentContext(
                project_id=project_id, agent_type=agent_type,
                previous_outputs=prev, documents=docs,
                api_config=api_cfg, erp_config=erp_cfg,
            )

    context = await _load_context()

    # Pass ERP config to tool executor so erp_create_entity etc. can connect
    from app.tools.registry import set_erp_config
    set_erp_config(context.erp_config)

    # Get tool definitions from agent config
    tool_defs = get_tool_definitions(agent.config.tools)

    # Match agent type to output schema
    schema_map = {
        "demand_parser": "app.schemas.agent_outputs.DemandOutput",
        "solution_generator": "app.schemas.agent_outputs.SolutionOutput",
        "system_config": "app.schemas.agent_outputs.ConfigOutput",
        "data_migration": "app.schemas.agent_outputs.MigrationOutput",
        "ops_qa": "app.schemas.agent_outputs.OpsOutput",
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        import importlib
        schema_name = schema_map.get(agent_type)
        if schema_name:
            mod_path, cls_name = schema_name.rsplit(".", 1)
            mod = importlib.import_module(mod_path)
            model_cls = getattr(mod, cls_name)
            schema = build_json_schema(model_cls)
        else:
            schema = {"type": "object", "properties": {}}

        user_task = _build_agent_task(agent_type, context)
        event_queue: asyncio.Queue = asyncio.Queue()

        # Auto-create tenant before system_config runs (don't rely on LLM)
        if agent_type == "system_config":
            erp_cfg = context.erp_config
            if not erp_cfg:
                await event_queue.put({"type": "error", "content": "ERP配置未设置！请在项目中关联ERP连接。"})
            else:
                await _ensure_tenant(event_queue, project, erp_cfg, project_id)

        # Run agent in background task — continues even if client disconnects
        async def run_agent():
            final_output = None
            stream_error = None
            try:
                async for event in agent_loop_stream(
                    system_prompt=agent.config.system_prompt,
                    user_task=user_task,
                    output_schema=schema,
                    tools=tool_defs,
                    tool_executor=execute_tool,
                    model=agent.config.llm_model,
                    api_config=context.api_config,
                ):
                    await event_queue.put(event)
                    if event.get("type") == "output":
                        final_output = event.get("content")
                    if event.get("type") == "error":
                        stream_error = event.get("content")
            except Exception as exc:
                logger.exception("Stream agent failed: %s", agent_type)
                stream_error = str(exc)
                await event_queue.put({"type": "error", "content": str(exc)})
            finally:
                await event_queue.put(None)  # Sentinel: agent done

                # Save result to DB
                try:
                    from app.database import async_session_factory
                    from app.models import ProjectAgent, AgentExecution, ErpConfig, Project
                    from app.tools.registry import set_erp_config
                    async with async_session_factory() as s:
                        pa = (await s.execute(
                            select(ProjectAgent).where(ProjectAgent.project_id == project_id, ProjectAgent.agent_type == agent_type)
                        )).scalar_one_or_none()
                        if pa:
                            if final_output:
                                pa.result_json = final_output if isinstance(final_output, dict) else {"raw_output": final_output}
                                pa.status = "completed"
                                pa.error_message = None
                            else:
                                pa.status = "failed"
                                pa.error_message = stream_error or "Unknown error"

                            execution = AgentExecution(
                                project_agent_id=pa.id,
                                attempt_number=(pa.retry_count or 0) + 1,
                                status=pa.status,
                            )
                            s.add(execution)

                            # Persist tenant_id to project record
                            from app.tools.registry import _current_erp_config
                            if _current_erp_config and _current_erp_config.get("tenant_id"):
                                prj = (await s.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
                                if prj:
                                    prj.tenant_id = _current_erp_config["tenant_id"]
                                    logger.info("Saved tenant_id=%s to project %s", prj.tenant_id, project_id)

                            await s.commit()
                except Exception as e:
                    logger.warning("Failed to save stream result: %s", e)

        bg_task = asyncio.ensure_future(run_agent())

        # Stream events to client while connected
        client_disconnected = False
        while not client_disconnected:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                if event is None:  # Sentinel: agent done
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                if await request.is_disconnected():
                    client_disconnected = True
                    logger.info("Client disconnected, agent continues in background for %s/%s", project_id, agent_type)
                    # Don't cancel bg_task — let it finish and save results

        # If client stayed connected, send done event
        if not client_disconnected:
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _ensure_tenant(event_queue, project, erp_cfg, project_id):
    """Verify or create a JEECG tenant for this project."""
    from app.tools.real_tools import ERPClient
    from app.tools.registry import _current_erp_config

    tid = project.tenant_id
    tenant_exists = False
    if tid:
        try:
            client = ERPClient()
            check = await client.request(
                "GET", f"{erp_cfg['base_url']}/sys/tenant/queryById",
                params={"id": tid}, erp_config=erp_cfg,
            )
            tenant_exists = check.get("success") and check.get("data", {}).get("success")
        except Exception:
            pass

    if tenant_exists:
        await event_queue.put({"type": "log", "content": f"已有租户ID={tid}，跳过创建"})
        return

    if tid:
        await event_queue.put({"type": "log", "content": f"租户ID={tid}已失效，重新创建"})
        project.tenant_id = None

    client = ERPClient()
    tenant_result = await client.create_entity(
        "tenant",
        {"name": project.name, "houseNumber": project_id[:12].upper(), "status": 1},
        erp_config=erp_cfg,
    )
    tid = tenant_result.get("tenant_id")
    if not tid:
        await event_queue.put({"type": "error", "content": f"创建租户失败: {tenant_result.get('error','')}"})
        return

    # Set status=1 and link admin
    for _ in range(2):
        try:
            await client.request("PUT", f"{erp_cfg['base_url']}/sys/tenant/edit",
                json_data={"id": tid, "status": 1}, erp_config=erp_cfg)
            await client.request("POST", f"{erp_cfg['base_url']}/sys/tenant/saveTenantJoinUser",
                json_data={"userId": "e9ca23d68d884d4ebb19d07889727dae", "tenantId": tid}, erp_config=erp_cfg)
            break
        except Exception:
            pass

    if _current_erp_config:
        _current_erp_config["tenant_id"] = str(tid)
    logger.info("Auto-created tenant %s for project %s", tid, project_id)
    await event_queue.put({"type": "log", "content": f"项目租户已创建 (ID={tid})，JEECG重新登录后切换租户"})


def _build_agent_task(agent_type: str, context: AgentContext) -> str:
    demand = context.previous_outputs.get("demand_parser", {})
    if agent_type == "demand_parser":
        docs_info = f"\n已上传文档: {json.dumps(context.documents, ensure_ascii=False)}" if context.documents else ""
        return f"分析ERP项目{context.project_id}的需求{docs_info}\n用web_search搜索行业信息，输出完整JSON。"
    elif agent_type == "solution_generator":
        return f"基于需求生成方案：{json.dumps(demand, ensure_ascii=False)}\n用web_search搜索类似案例，调用generate_ppt和generate_excel，输出JSON。"
    elif agent_type == "system_config":
        solution = context.previous_outputs.get("solution_generator", {})
        return f"配置ERP系统：需求={json.dumps(demand, ensure_ascii=False)}，方案={json.dumps(solution, ensure_ascii=False)}\n用web_search搜索配置最佳实践，调用erp_create_entity创建组织，输出JSON。"
    elif agent_type == "data_migration":
        return f"执行数据迁移：{json.dumps(demand.get('modules', []), ensure_ascii=False)}\n按顺序调用read_excel_data→auto_map_fields→clean_data→detect_duplicates→erp_batch_upsert→generate_excel，输出JSON。"
    elif agent_type == "ops_qa":
        return f"执行运维初始化：{json.dumps(context.previous_outputs, ensure_ascii=False)}\n调用check_health→search_logs→search_knowledge→send_wecom_message→index_knowledge，输出JSON。"
    return f"Execute task for project {context.project_id}"
