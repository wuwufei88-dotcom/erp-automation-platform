from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


class AgentContext(BaseModel):
    project_id: str
    agent_type: str
    previous_outputs: dict[str, dict] = {}
    documents: list[str] = []
    api_config: dict | None = None
    erp_config: dict | None = None


@dataclass
class AgentResult:
    success: bool
    output: dict | None = None
    error: str | None = None
    logs: list[dict] = field(default_factory=list)


@dataclass
class AgentConfig:
    agent_id: str
    display_name: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    output_schema: str = ""
    llm_model: str = ""
    max_retries: int = 2
    timeout_seconds: int = 600


class BaseAgent(ABC):
    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult: ...

    def validate_output(self, result: AgentResult) -> bool:
        if not result.success:
            return False
        return result.output is not None

    @property
    def bound_tools(self) -> list[str]:
        return list(self.config.tools)
