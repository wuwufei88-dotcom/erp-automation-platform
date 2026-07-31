from __future__ import annotations

import logging
import os
from typing import Optional

import yaml

from app.agents.base import AgentConfig, BaseAgent
from app.agents.demand_parser import DemandParserAgent
from app.agents.solution_generator import SolutionGeneratorAgent
from app.agents.system_config import SystemConfigAgent
from app.agents.data_migration import DataMigrationAgent
from app.agents.ops_qa import OpsQAAgent

logger = logging.getLogger(__name__)

_agent_classes: dict[str, type[BaseAgent]] = {
    "demand_parser": DemandParserAgent,
    "solution_generator": SolutionGeneratorAgent,
    "system_config": SystemConfigAgent,
    "data_migration": DataMigrationAgent,
    "ops_qa": OpsQAAgent,
}

_registry: dict[str, BaseAgent] = {}


def load_agent_config(agent_id: str, config_dir: str) -> AgentConfig:
    config_path = os.path.join(config_dir, f"{agent_id}.yaml")
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return AgentConfig(
            agent_id=data.get("agent_id", agent_id),
            display_name=data.get("display_name", agent_id),
            system_prompt=data.get("system_prompt", ""),
            tools=data.get("tools", []),
            output_schema=data.get("output_schema", ""),
            llm_model=data.get("llm_model", ""),
            max_retries=data.get("max_retries", 2),
            timeout_seconds=data.get("timeout_seconds", 600),
        )

    return AgentConfig(
        agent_id=agent_id,
        display_name=agent_id,
        system_prompt="",
        tools=[],
        output_schema="",
        llm_model="",
    )


def init_registry(config_dir: str) -> None:
    for agent_id, agent_cls in _agent_classes.items():
        config = load_agent_config(agent_id, config_dir)
        _registry[agent_id] = agent_cls(config)
        logger.info("Registered agent: %s", agent_id)


def get_agent(agent_type: str) -> Optional[BaseAgent]:
    return _registry.get(agent_type)
