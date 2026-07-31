from __future__ import annotations

import json
import logging

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.llm import agent_loop, build_json_schema
from app.agents.safe_parse import safe_parse
from app.schemas.agent_outputs import OpsOutput
from app.tools.registry import execute_tool, get_tool_definitions

logger = logging.getLogger(__name__)

TOOLS = ["search_knowledge", "search_logs", "check_health", "send_wecom_message", "index_knowledge"]


class OpsQAAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        logs: list[dict] = []
        try:
            all_outputs = context.previous_outputs
            logs.append({"level": "info", "message": "初始化运维知识库"})

            system_prompt = self.config.system_prompt + """
可用工具：
- check_health: 检查系统端点健康状态
- search_logs: 搜索错误日志
- search_knowledge: 搜索运维FAQ和解决方案
- send_wecom_message: 发送企业微信告警
- index_knowledge: 将新知识索引到知识库

工作流程：检查健康→搜索日志→搜索知识库→发现严重问题则推送告警→索引新知识→输出运维报告。"""

            user_task = f"""执行ERP项目上线后运维初始化。

项目交付结果：{json.dumps(all_outputs, ensure_ascii=False, indent=2)}

调用工具执行以下任务，最终输出JSON（query/answer/sources/diagnosis/alert_sent）：

1. check_health 检查以下端点：
   - 平台后端: http://localhost:8000/api/projects （必须检查，这是本平台自身）
   - ERP系统: 如果项目配置了ERP连接则检查对应URL，否则跳过
2. search_logs 搜索近期错误日志
3. search_knowledge 搜索运维最佳实践
4. send_wecom_message: 仅在发现严重故障（平台本身或ERP不可用）时才推送告警
5. index_knowledge: 索引本次运维发现

注意：
- 平台后端 http://localhost:8000 是本系统自身，应始终健康
- 企业微信 Webhook 未配置时可以跳过，不算故障
- 没有配置ERP时不要虚构ERP端点检查
- 输出尽量简洁，不要虚构不存在的服务故障"""

            tool_defs = get_tool_definitions(TOOLS)
            schema = build_json_schema(OpsOutput)
            output = await agent_loop(
                system_prompt=system_prompt, user_task=user_task,
                output_schema=schema, tools=tool_defs, tool_executor=execute_tool,
                model=self.config.llm_model, api_config=context.api_config,
            )

            output["query"] = "ERP项目交付完成，初始化运维问答知识库"
            validated = safe_parse(output, OpsOutput)
            logs.append({"level": "info", "message": "运维初始化完成"})
            return AgentResult(success=True, output=validated.model_dump(), logs=logs)

        except Exception as exc:
            logger.exception("OpsQAAgent failed")
            return AgentResult(success=False, error=str(exc), logs=logs)
