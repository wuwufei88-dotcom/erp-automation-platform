from __future__ import annotations

from enum import Enum


class ProjectState(str, Enum):
    NEW = "new"
    DEMAND_PARSE = "demand_parse"
    SOLUTION_GENERATE = "solution_generate"
    SYSTEM_CONFIG = "system_config"
    DATA_MIGRATION = "data_migration"
    OPS_QA = "ops_qa"
    COMPLETED = "completed"
    FAILED = "failed"


TRANSITIONS: dict[ProjectState, list[ProjectState]] = {
    ProjectState.NEW: [ProjectState.DEMAND_PARSE, ProjectState.FAILED],
    ProjectState.DEMAND_PARSE: [ProjectState.SOLUTION_GENERATE, ProjectState.FAILED],
    ProjectState.SOLUTION_GENERATE: [ProjectState.SYSTEM_CONFIG, ProjectState.FAILED],
    ProjectState.SYSTEM_CONFIG: [ProjectState.DATA_MIGRATION, ProjectState.FAILED],
    ProjectState.DATA_MIGRATION: [ProjectState.OPS_QA, ProjectState.FAILED],
    ProjectState.OPS_QA: [ProjectState.COMPLETED, ProjectState.FAILED],
    ProjectState.COMPLETED: [],
    ProjectState.FAILED: [],
}

AGENT_FOR_STATE: dict[ProjectState, str] = {
    ProjectState.DEMAND_PARSE: "demand_parser",
    ProjectState.SOLUTION_GENERATE: "solution_generator",
    ProjectState.SYSTEM_CONFIG: "system_config",
    ProjectState.DATA_MIGRATION: "data_migration",
    ProjectState.OPS_QA: "ops_qa",
}

NEXT_STATE: dict[ProjectState, ProjectState | None] = {
    ProjectState.NEW: ProjectState.DEMAND_PARSE,
    ProjectState.DEMAND_PARSE: ProjectState.SOLUTION_GENERATE,
    ProjectState.SOLUTION_GENERATE: ProjectState.SYSTEM_CONFIG,
    ProjectState.SYSTEM_CONFIG: ProjectState.DATA_MIGRATION,
    ProjectState.DATA_MIGRATION: ProjectState.OPS_QA,
    ProjectState.OPS_QA: ProjectState.COMPLETED,
    ProjectState.COMPLETED: None,
    ProjectState.FAILED: None,
}


def can_transition(current: ProjectState, target: ProjectState) -> bool:
    return target in TRANSITIONS.get(current, [])


def next_state(current: ProjectState) -> ProjectState:
    return NEXT_STATE.get(current, current)
