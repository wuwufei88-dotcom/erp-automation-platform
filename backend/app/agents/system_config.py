from __future__ import annotations

import json
import logging

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.llm import agent_loop, build_json_schema
from app.agents.safe_parse import safe_parse
from app.config import get_settings
from app.schemas.agent_outputs import ConfigOutput
from app.tools.registry import execute_tool, get_tool_definitions, set_erp_config

logger = logging.getLogger(__name__)

TOOLS = ["erp_health_check", "erp_create_entity", "search_knowledge"]

SYSTEM_CONFIG_PROMPT = """你是ERP系统配置专家。你有能力调用真实工具来配置ERP系统。

## 核心规则（违反将导致配置无效）

1. **禁止编造输出**：你输出的每一个 configured_orgs 条目、每一个 config_log 消息，都必须来自真实的工具调用结果
2. **必须先调用工具再输出**：在输出最终JSON之前，你必须至少调用 erp_health_check 一次
3. **工具返回什么就记录什么**：不要把工具返回的成功状态改成失败，也不要把失败改成成功

## 执行流程（严格按顺序）

Step 1: 调用 erp_health_check 检查ERP系统健康状态
   - 如果失败（success=false），在 config_log 中记录错误，manual_items 中说明需要人工介入

Step 2: 从用户输入的需求JSON中提取 org_structure 列表
   - 对每一个组织节点，调用 erp_create_entity(entity_type="org", data={...})
   - data格式：{"departName": "组织名称", "orgCode": "编码", "parentId": "父节点ID", "orgCategory": "2", "orgType": "2"}
   - 将工具返回的结果直接记录到 configured_orgs 中

Step 3: 调用 search_knowledge 搜索ERP配置最佳实践

Step 4: 输出最终JSON"""


class SystemConfigAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        logs: list[dict] = []
        try:
            if context.erp_config:
                set_erp_config(context.erp_config)
                logs.append({"level": "info", "message": f"ERP配置已设置: {context.erp_config.get('base_url')}"})

            demand = context.previous_outputs.get("demand_parser", {})
            solution = context.previous_outputs.get("solution_generator", {})
            org_structure = demand.get("org_structure", [])
            logs.append({"level": "info", "message": f"待配置{len(org_structure)}个组织节点"})

            erp_info = ""
            if context.erp_config:
                erp_info = f"""
当前ERP连接信息：
  base_url: {context.erp_config.get('base_url')}
  provider: {context.erp_config.get('provider')}
  auth_type: {context.erp_config.get('auth_type')}
  状态: 已连接"""

            user_task = f"""执行ERP系统配置。你必须调用工具，禁止跳过。

{erp_info}

需求解析结果（包含待创建的组织架构）：
{json.dumps(demand, ensure_ascii=False, indent=2)}

实施方案：
{json.dumps(solution.get('plan_summary', ''), ensure_ascii=False)}

请立即开始Step 1：调用 erp_health_check 检查系统状态。
然后对每个组织节点调用 erp_create_entity。
最后输出配置结果JSON。"""

            tool_defs = get_tool_definitions(TOOLS)
            schema = build_json_schema(ConfigOutput)
            settings = get_settings()
            output = await agent_loop(
                system_prompt=SYSTEM_CONFIG_PROMPT,
                user_task=user_task,
                output_schema=schema,
                tools=tool_defs,
                tool_executor=execute_tool,
                model=settings.llm_default_model,
                api_config=context.api_config,
            )

            validated = safe_parse(output, ConfigOutput)
            created_count = len([o for o in validated.configured_orgs if o.status == "created"])
            logs.append({"level": "info", "message": f"配置完成: {created_count}/{len(validated.configured_orgs)}个组织创建成功"})
            return AgentResult(success=True, output=validated.model_dump(), logs=logs)

        except Exception as exc:
            logger.exception("SystemConfigAgent failed")
            return AgentResult(success=False, error=str(exc), logs=logs)
