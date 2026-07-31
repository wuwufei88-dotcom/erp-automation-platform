# Tool registry with OpenAI-compatible Function Calling schemas
# Each tool definition includes: name, description, parameters (JSON Schema)

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

from app.tools.real_tools import (
    DataProcessor,
    DocumentParser,
    DocumentWriter,
    ERPClient,
    KnowledgeBase,
    LogAnalyzer,
    NotificationService,
)
from app.agents.stream import web_search

_doc_parser = DocumentParser()
_doc_writer = DocumentWriter()
_data_proc = DataProcessor()
_erp = ERPClient()
_kb = KnowledgeBase()
_notify = NotificationService()
_logs = LogAnalyzer()

_current_erp_config: dict | None = None


def set_erp_config(config: dict | None) -> None:
    global _current_erp_config
    _current_erp_config = config


# ─── Tool Registry ────────────────────────────────────────────

TOOLS: dict[str, dict] = {
    # ── Document Tools ──
    "parse_document": {
        "definition": {
            "name": "parse_document",
            "description": "解析上传的文档文件（PDF/DOCX/PPTX/TXT/XLSX），提取文本内容和结构信息。用于读取客户需求文档、技术规格书等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "文档文件的绝对路径"},
                },
                "required": ["file_path"],
            },
        },
        "handler": lambda **kw: _doc_parser.parse(kw["file_path"]),
    },
    "generate_ppt": {
        "definition": {
            "name": "generate_ppt",
            "description": "生成 PPT 演示文稿。传入幻灯片内容列表和输出路径，生成 .pptx 文件。用于生成项目方案汇报、培训课件等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "slides": {"type": "array", "items": {"type": "object"}, "description": "幻灯片列表，每项包含 title 和 content"},
                    "output_path": {"type": "string", "description": "输出文件路径，如 /tmp/solution.pptx"},
                    "template_path": {"type": "string", "description": "可选：PPT 模板路径"},
                },
                "required": ["slides", "output_path"],
            },
        },
        "handler": lambda **kw: _doc_writer.write_ppt(kw.get("slides", []), kw["output_path"], kw.get("template_path", "")),
    },
    "generate_excel": {
        "definition": {
            "name": "generate_excel",
            "description": "生成 Excel 工作簿。传入多个 sheet 的数据，生成 .xlsx 文件。用于生成报价单、数据报表、错误报告等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "sheets": {"type": "object", "description": "{sheet名称: [{列名: 值}]} 的字典"},
                    "output_path": {"type": "string", "description": "输出文件路径"},
                },
                "required": ["sheets", "output_path"],
            },
        },
        "handler": lambda **kw: _doc_writer.write_excel(kw["sheets"], kw["output_path"]),
    },

    # ── Data Tools ──
    "read_excel_data": {
        "definition": {
            "name": "read_excel_data",
            "description": "读取 Excel/CSV 文件，返回数据预览、列信息、数据类型和空值统计。用于数据迁移前探查客户数据质量。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Excel 文件路径"},
                    "sheet_name": {"type": "string", "description": "工作表名称（可选，默认第一个）"},
                },
                "required": ["file_path"],
            },
        },
        "handler": lambda **kw: _data_proc.read_excel(kw["file_path"], kw.get("sheet_name", "")),
    },
    "clean_data": {
        "definition": {
            "name": "clean_data",
            "description": "清洗数据：去除空格、统一大小写、填充空值。传入数据行列表和清洗规则。",
            "parameters": {
                "type": "object",
                "properties": {
                    "rows": {"type": "array", "items": {"type": "object"}, "description": "数据行列表"},
                    "rules": {"type": "object", "description": "清洗规则，如 {'column_name': {'trim': true, 'uppercase': true, 'fill_empty': 'N/A'}}"},
                },
                "required": ["rows", "rules"],
            },
        },
        "handler": lambda **kw: _data_proc.clean_data(kw["rows"], kw["rules"]),
    },
    "detect_duplicates": {
        "definition": {
            "name": "detect_duplicates",
            "description": "检测数据中的重复行。指定关键列，返回重复行的索引列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "rows": {"type": "array", "items": {"type": "object"}, "description": "数据行列表"},
                    "key_columns": {"type": "array", "items": {"type": "string"}, "description": "用于判断重复的关键列名"},
                },
                "required": ["rows", "key_columns"],
            },
        },
        "handler": lambda **kw: _data_proc.detect_duplicates(kw["rows"], kw["key_columns"]),
    },
    "auto_map_fields": {
        "definition": {
            "name": "auto_map_fields",
            "description": "自动映射源字段到目标字段。使用模糊匹配算法，返回映射关系和置信度。用于将客户 Excel 列名映射到 ERP 标准字段。",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_columns": {"type": "array", "items": {"type": "string"}, "description": "源文件的列名列表"},
                    "target_schema": {"type": "object", "description": "目标 schema，格式: {'目标字段': ['别名1', '别名2']}"},
                },
                "required": ["source_columns", "target_schema"],
            },
        },
        "handler": lambda **kw: _data_proc.auto_map_fields(kw["source_columns"], kw["target_schema"]),
    },

    # ── ERP API Tools ──
    "erp_create_entity": {
        "definition": {
            "name": "erp_create_entity",
            "description": "在 ERP 系统中创建实体（组织、用户、科目等）。自动使用项目关联的 ERP 配置进行认证。",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "description": "实体类型，如 org, user, account, approval_flow"},
                    "data": {"type": "object", "description": "实体的属性数据"},
                },
                "required": ["entity_type", "data"],
            },
        },
        "handler": lambda **kw: _erp.create_entity(kw["entity_type"], kw["data"], kw.get("base_url", ""), _current_erp_config),
    },
    "erp_batch_upsert": {
        "definition": {
            "name": "erp_batch_upsert",
            "description": "批量导入数据到 ERP 系统。自动分批（每批100条），返回导入统计和错误明细。自动使用项目关联的 ERP 配置进行认证。",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "description": "实体类型"},
                    "rows": {"type": "array", "items": {"type": "object"}, "description": "数据行列表"},
                },
                "required": ["entity_type", "rows"],
            },
        },
        "handler": lambda **kw: _erp.batch_upsert(kw["entity_type"], kw["rows"], kw.get("base_url", ""), _current_erp_config),
    },
    "erp_health_check": {
        "definition": {
            "name": "erp_health_check",
            "description": "检查 ERP 系统健康状态。调用 health 端点确认系统可用。自动使用项目关联的 ERP 配置。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        "handler": lambda **kw: _erp.health_check(kw.get("base_url", ""), _current_erp_config),
    },

    # ── Knowledge Tools ──
    "search_knowledge": {
        "definition": {
            "name": "search_knowledge",
            "description": "在 ERP 知识库中语义搜索相关内容。用于查找历史案例、运维FAQ、实施最佳实践等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询文本"},
                    "top_k": {"type": "integer", "description": "返回结果数量，默认5"},
                },
                "required": ["query"],
            },
        },
        "handler": lambda **kw: _kb.search(kw["query"], top_k=kw.get("top_k", 5)),
    },
    "index_knowledge": {
        "definition": {
            "name": "index_knowledge",
            "description": "将新知识条目索引到知识库中，供后续检索使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "知识内容文本"},
                    "metadata": {"type": "object", "description": "元数据（标题、标签、来源等）"},
                },
                "required": ["content", "metadata"],
            },
        },
        "handler": lambda **kw: _kb.index_document(kw["content"], kw["metadata"]),
    },

    # ── Notification Tools ──
    "send_wecom_message": {
        "definition": {
            "name": "send_wecom_message",
            "description": "通过企业微信机器人发送消息。支持文本和 Markdown 格式。用于推送告警、通知关键节点完成等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "消息内容"},
                    "msg_type": {"type": "string", "description": "消息类型: text 或 markdown，默认 text"},
                    "webhook_url": {"type": "string", "description": "Webhook URL（可选，使用默认配置）"},
                },
                "required": ["content"],
            },
        },
        "handler": lambda **kw: _notify.send_wecom(kw["content"], kw.get("msg_type", "text"), kw.get("webhook_url", "")),
    },

    # ── Log & Monitor Tools ──
    "search_logs": {
        "definition": {
            "name": "search_logs",
            "description": "搜索系统日志中的特定模式。用于故障排查和诊断。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "搜索关键词或正则模式"},
                    "time_range_hours": {"type": "integer", "description": "搜索时间范围（小时），默认24"},
                },
                "required": ["pattern"],
            },
        },
        "handler": lambda **kw: _logs.search_logs(kw["pattern"], time_range_hours=kw.get("time_range_hours", 24)),
    },
    "check_health": {
        "definition": {
            "name": "check_health",
            "description": "检查多个系统端点的健康状态。返回每个端点的 HTTP 状态码和健康判定。",
            "parameters": {
                "type": "object",
                "properties": {
                    "endpoints": {"type": "array", "items": {"type": "string"}, "description": "要检查的URL列表"},
                },
                "required": ["endpoints"],
            },
        },
        "handler": lambda **kw: _logs.check_system_health(kw["endpoints"]),
    },
    # ── Web Search ──
    "web_search": {
        "definition": {
            "name": "web_search",
            "description": "搜索互联网获取最新信息。用于查询行业动态、ERP最佳实践、技术方案等。免费，无需API Key。每次搜索返回标题、URL和摘要。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "返回结果数量，默认5，最大10"},
                },
                "required": ["query"],
            },
        },
        "handler": lambda **kw: web_search(kw["query"], kw.get("max_results", 5)),
    },
}


def get_tool_definitions(tool_names: list[str]) -> list[dict]:
    """Get Function Calling tool definitions for the given tool names."""
    defs = []
    for name in tool_names:
        if name in TOOLS:
            defs.append({"type": "function", "function": TOOLS[name]["definition"]})
    return defs


async def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a tool by name with the given arguments."""
    global _current_erp_config
    if name not in TOOLS:
        return {"success": False, "error": f"Unknown tool: {name}"}
    handler = TOOLS[name]["handler"]
    try:
        if callable(handler):
            result = handler(**arguments)
            import inspect
            if inspect.iscoroutine(result):
                result = await result
            # If tenant was created, update current ERP config so subsequent calls use it
            if isinstance(result, dict) and result.get("tenant_id") and _current_erp_config:
                _current_erp_config["tenant_id"] = str(result["tenant_id"])
                logger.info("ERP tenant updated: %s", result["tenant_id"])
            return result
        return {"success": False, "error": f"Handler for {name} is not callable"}
    except Exception as e:
        logger.exception("Tool %s failed", name)
        return {"success": False, "error": str(e)}
