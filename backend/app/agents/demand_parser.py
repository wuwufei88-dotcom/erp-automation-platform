from __future__ import annotations

import json
import logging

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.llm import agent_loop, build_json_schema
from app.agents.safe_parse import safe_parse
from app.schemas.agent_outputs import DemandOutput
from app.tools.registry import execute_tool, get_tool_definitions

logger = logging.getLogger(__name__)

TOOLS = ["parse_document", "search_knowledge", "web_search"]


class DemandParserAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        logs: list[dict] = []
        try:
            docs_info = ""
            if context.documents:
                logs.append({"level": "info", "message": f"读取{len(context.documents)}份需求文档"})
                docs_info = f"\n已上传文档: {json.dumps(context.documents, ensure_ascii=False)}\n先用 parse_document 解析文档，再调用 search_knowledge 搜索行业案例作为补充。"

            system_prompt = self.config.system_prompt + """
可用工具：
- parse_document: 解析上传的PDF/DOCX/PPTX/TXT文档，提取文本内容
- search_knowledge: 搜索ERP实施知识库，获取行业案例和最佳实践

工作流程：
1. 如果有上传文档，先调用 parse_document 解析
2. 调用 search_knowledge 搜索相关行业案例
3. 综合所有信息，最终输出JSON结果"""

            user_task = f"""分析ERP项目需求并输出JSON。

项目ID: {context.project_id}{docs_info}

输出字段（必须填充真实数据，不要空数组）：
- org_structure: 4-6个组织节点(name/code/parent_code/node_type)
- modules: 3-5个模块(module_name/priority/notes)
- customizations: 2-3个定制需求(title/description/is_standard_config)
- timeline: 4-5个阶段(phase/estimated_days/description)
- ambiguities: 2-3个待确认问题(字符串列表)"""

            tool_defs = get_tool_definitions(TOOLS)
            schema = build_json_schema(DemandOutput)

            output = await agent_loop(
                system_prompt=system_prompt,
                user_task=user_task,
                output_schema=schema,
                tools=tool_defs,
                tool_executor=execute_tool,
                model=self.config.llm_model,
                api_config=context.api_config,
            )

            validated = safe_parse(output, DemandOutput)
            logs.append({"level": "info", "message": f"需求解析完成: {len(validated.modules)}个模块, {len(validated.org_structure)}个组织"})
            return AgentResult(success=True, output=validated.model_dump(), logs=logs)

        except Exception as exc:
            logger.exception("DemandParserAgent failed")
            return AgentResult(success=False, error=str(exc), logs=logs)
