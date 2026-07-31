from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentParserTool:
    async def parse(self, file_paths: list[str]) -> str:
        logger.info("Parsing documents: %s", file_paths)
        return f"[Parsed content from {len(file_paths)} documents]"


class PPTGeneratorTool:
    async def generate(self, content: dict, output_path: str) -> str:
        logger.info("Generating PPT: %s", output_path)
        return output_path


class ExcelHandlerTool:
    async def read(self, file_path: str) -> list[dict]:
        logger.info("Reading Excel: %s", file_path)
        return []

    async def write(self, data: list[dict], output_path: str) -> str:
        logger.info("Writing Excel: %s", output_path)
        return output_path


class FieldMapperTool:
    async def auto_map(self, source_columns: list[str], target_schema: dict) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for col in source_columns:
            for target, aliases in target_schema.items():
                if col in aliases:
                    mapping[col] = target
                    break
        return mapping


class ERPClientTool:
    async def create_org(self, org_data: dict) -> dict:
        logger.info("Creating org: %s", org_data.get("name"))
        return {"id": f"ORG-{org_data.get('code', 'XXX')}", "status": "created"}

    async def configure_module(self, module_name: str, settings: dict) -> dict:
        logger.info("Configuring module: %s", module_name)
        return {"module": module_name, "status": "configured"}

    async def create_approval_flow(self, flow_data: dict) -> dict:
        logger.info("Creating approval flow: %s", flow_data.get("name"))
        return {"id": f"FLOW-{flow_data.get('name', 'XXX')}", "status": "created"}

    async def batch_upsert(self, entity_type: str, rows: list[dict]) -> dict:
        logger.info("Batch upsert %s: %d rows", entity_type, len(rows))
        return {"imported": len(rows), "failed": 0}


class LogSearchTool:
    async def query(self, pattern: str, time_range_hours: int = 24) -> list[dict]:
        logger.info("Log search: pattern=%s, hours=%d", pattern, time_range_hours)
        return []


class WeChatWorkTool:
    async def send_message(self, content: str, receivers: Optional[list[str]] = None) -> bool:
        logger.info("WeChat Work message: %s", content[:50])
        return True

    async def send_alert(self, title: str, detail: str) -> bool:
        logger.info("WeChat Work alert: %s", title)
        return True
