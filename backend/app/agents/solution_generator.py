from __future__ import annotations

import json
import logging

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.llm import agent_loop, build_json_schema
from app.agents.safe_parse import safe_parse
from app.schemas.agent_outputs import SolutionOutput
from app.tools.registry import execute_tool, get_tool_definitions

logger = logging.getLogger(__name__)

TOOLS = ["search_knowledge", "generate_ppt", "generate_excel"]


class SolutionGeneratorAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        logs: list[dict] = []
        try:
            demand = context.previous_outputs.get("demand_parser", {})
            logs.append({"level": "info", "message": f"基于需求生成方案: {len(demand.get('modules',[]))}个模块"})

            system_prompt = self.config.system_prompt + """
可用工具：
- search_knowledge: 搜索历史项目案例和方案模板
- generate_ppt: 生成方案汇报PPT
- generate_excel: 生成报价单Excel

工作流程：先搜索历史案例作为参考，然后生成PPT和Excel，最后输出完整JSON。"""

            user_task = f"""基于需求生成实施方案JSON。

需求数据：{json.dumps(demand, ensure_ascii=False, indent=2)}

输出字段：plan_summary/phases/pricing/training_schedule/risks/ppt_url/excel_url
请调用工具生成交付物，然后输出完整JSON。"""

            tool_defs = get_tool_definitions(TOOLS)
            schema = build_json_schema(SolutionOutput)
            output = await agent_loop(
                system_prompt=system_prompt, user_task=user_task,
                output_schema=schema, tools=tool_defs, tool_executor=execute_tool,
                model=self.config.llm_model, api_config=context.api_config,
            )

            validated = safe_parse(output, SolutionOutput)
            logs.append({"level": "info", "message": f"方案生成完成: {len(validated.phases)}个阶段"})
            return AgentResult(success=True, output=validated.model_dump(), logs=logs)

        except Exception as exc:
            logger.exception("SolutionGeneratorAgent failed")
            return AgentResult(success=False, error=str(exc), logs=logs)
