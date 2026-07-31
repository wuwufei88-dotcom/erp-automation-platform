from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrgNode(BaseModel):
    name: str = ""
    code: str = ""
    parent_code: Optional[str] = None
    node_type: str = "department"


class ModuleRequirement(BaseModel):
    module_name: str = ""
    priority: str = "required"
    notes: Optional[str] = None


class CustomizationPoint(BaseModel):
    title: str = ""
    description: str = ""
    is_standard_config: bool = False


class TimelineEstimate(BaseModel):
    phase: str = ""
    estimated_days: int = 30
    description: Optional[str] = None


class Ambiguity(BaseModel):
    question: str = ""


class DemandOutput(BaseModel):
    org_structure: list[OrgNode] = []
    modules: list[ModuleRequirement] = []
    customizations: list[CustomizationPoint] = []
    timeline: list[TimelineEstimate] = []
    ambiguities: list[str] = []


class ImplementationPhase(BaseModel):
    name: str = ""
    duration_days: int = 30
    resources: list[str] = []
    deliverables: list[str] = []


class PricingBreakdown(BaseModel):
    license_fee: float = 0
    implementation_fee: float = 0
    training_fee: float = 0
    total: float = 0


class TrainingSession(BaseModel):
    topic: str = ""
    audience: str = ""
    duration_hours: float = 0.0
    scheduled_week: int = 0


class RiskItem(BaseModel):
    description: str = ""
    severity: str = "medium"
    mitigation: Optional[str] = None


class SolutionOutput(BaseModel):
    plan_summary: str = ""
    phases: list[ImplementationPhase] = []
    pricing: PricingBreakdown = Field(default_factory=PricingBreakdown)
    training_schedule: list[TrainingSession] = []
    risks: list[RiskItem] = []
    ppt_url: Optional[str] = None
    excel_url: Optional[str] = None


class ConfiguredOrg(BaseModel):
    name: str = ""
    org_id: Optional[str] = None
    status: str = "created"


class ApprovalFlowConfig(BaseModel):
    name: str = ""
    flow_id: Optional[str] = None
    steps: int = 0


class ModuleConfig(BaseModel):
    module_name: str = ""
    settings: dict = {}
    status: str = "configured"


class ManualConfigItem(BaseModel):
    title: str = ""
    reason: str = ""


class ConfigOutput(BaseModel):
    configured_orgs: list[ConfiguredOrg] = []
    approval_flows: list[ApprovalFlowConfig] = []
    module_settings: list[ModuleConfig] = []
    manual_items: list[ManualConfigItem] = []
    config_log: list[str] = []


class MigrationError(BaseModel):
    row_number: int = 0
    column: str = ""
    value: Optional[str] = None
    reason: str = ""


class MigrationOutput(BaseModel):
    total_rows: int = 0
    imported_rows: int = 0
    failed_rows: int = 0
    field_mapping: dict[str, str] = {}
    duplicates_found: int = 0
    errors: list[MigrationError] = []
    error_report_url: Optional[str] = None


class KnowledgeSource(BaseModel):
    title: str = ""
    relevance: float = 0.0


class DiagnosisResult(BaseModel):
    fault_type: str = ""
    confidence: float = 0.0
    recommendation: str = ""


class OpsOutput(BaseModel):
    query: str
    answer: str
    sources: list[KnowledgeSource] = []
    diagnosis: Optional[DiagnosisResult] = None
    alert_sent: bool = False
