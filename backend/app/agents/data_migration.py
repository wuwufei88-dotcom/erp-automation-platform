from __future__ import annotations

import json
import logging

from app.agents.base import AgentContext, AgentResult, BaseAgent
from app.agents.llm import agent_loop, build_json_schema
from app.agents.safe_parse import safe_parse
from app.config import get_settings
from app.schemas.agent_outputs import MigrationOutput
from app.tools.registry import execute_tool, get_tool_definitions, set_erp_config

logger = logging.getLogger(__name__)

TOOLS = ["read_excel_data", "auto_map_fields", "clean_data", "detect_duplicates", "erp_batch_upsert", "generate_excel"]

DATA_MIGRATION_PROMPT = """你是ERP数据迁移专家。你有能力调用真实工具来执行数据迁移任务。

## 核心规则（违反将导致迁移失败）

1. **禁止编造输出**：你输出的 total_rows/imported_rows/failed_rows/field_mapping/errors 都必须来自真实的工具调用结果
2. **必须先调用工具再输出**：在输出最终JSON之前，你必须按顺序调用迁移工具链
3. **工具返回什么就记录什么**：不要把工具返回的统计数字改成编造的数字

## 执行流程（严格按顺序，不可跳过）

Step 1: 调用 read_excel_data(file_path="文档路径") 读取用户上传的数据文件
   - 文档路径从用户输入中的 documents 列表获取
   - 如果读取失败，在 errors 中记录并终止

Step 2: 调用 auto_map_fields(source_columns=[...], target_entity="实体类型")
   - 将源文件的列映射到ERP系统的标准字段
   - 记录 field_mapping 结果

Step 3: 调用 clean_data(rows=..., rules=...) 清洗数据
   - 去空格、格式化、填充默认值

Step 4: 调用 detect_duplicates(rows=..., key_fields=[...]) 检测重复

Step 5: 调用 erp_batch_upsert(entity_type="实体类型", rows=[...]) 批量导入ERP
   - 每批最多100条
   - 记录成功/失败数量

Step 6: 如果有失败记录，调用 generate_excel 生成错误报告

Step 7: 输出最终JSON。所有数字必须等于工具返回值的累加。"""


class DataMigrationAgent(BaseAgent):
    async def execute(self, context: AgentContext) -> AgentResult:
        logs: list[dict] = []
        try:
            if context.erp_config:
                set_erp_config(context.erp_config)
                logs.append({"level": "info", "message": f"ERP配置已设置: {context.erp_config.get('base_url')}"})

            demand = context.previous_outputs.get("demand_parser", {})
            config = context.previous_outputs.get("system_config", {})
            logs.append({"level": "info", "message": "开始数据迁移"})

            # Build document list for the LLM
            doc_list = ""
            if context.documents:
                docs = []
                for d in context.documents:
                    file_path = getattr(d, 'minio_key', '') or getattr(d, 'filename', '')
                    docs.append(f"  - {file_path}")
                if docs:
                    doc_list = "\n可用的数据文件：\n" + "\n".join(docs)

            erp_info = ""
            if context.erp_config:
                erp_info = f"""
当前ERP连接信息：
  base_url: {context.erp_config.get('base_url')}
  provider: {context.erp_config.get('provider')}
  auth_type: {context.erp_config.get('auth_type')}
  状态: 已连接"""

            user_task = f"""执行数据迁移任务。你必须按顺序调用工具，禁止跳过任何步骤。

{erp_info}
{doc_list}

需求数据：
{json.dumps(demand, ensure_ascii=False, indent=2)}

系统配置结果：
{json.dumps(config, ensure_ascii=False)}

请立即开始Step 1：读取数据文件，然后依次执行映射、清洗、去重、导入。
最后输出完整的迁移结果JSON。"""

            tool_defs = get_tool_definitions(TOOLS)
            schema = build_json_schema(MigrationOutput)
            settings = get_settings()
            output = await agent_loop(
                system_prompt=DATA_MIGRATION_PROMPT,
                user_task=user_task,
                output_schema=schema,
                tools=tool_defs,
                tool_executor=execute_tool,
                model=settings.llm_default_model,
                api_config=context.api_config,
            )

            validated = safe_parse(output, MigrationOutput)
            logs.append({"level": "info", "message": f"迁移完成: {validated.imported_rows}/{validated.total_rows}条"})
            return AgentResult(success=True, output=validated.model_dump(), logs=logs)

        except Exception as exc:
            logger.exception("DataMigrationAgent failed")
            return AgentResult(success=False, error=str(exc), logs=logs)
