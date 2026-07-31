from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    api_config_id: Optional[int] = None
    erp_config_id: Optional[int] = None


class ProjectRead(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    api_config_id: Optional[int] = None
    erp_config_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProjectDetailRead(ProjectRead):
    agents: list["AgentRead"] = []


class AgentRead(BaseModel):
    id: str
    agent_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    error_message: Optional[str]
    result_json: Optional[dict] = None

    model_config = {"from_attributes": True}


class AgentExecutionRead(BaseModel):
    id: str
    attempt_number: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]

    model_config = {"from_attributes": True}


class AgentLogRead(BaseModel):
    id: int
    level: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: str
    filename: str
    mime_type: Optional[str]
    size_bytes: Optional[int]
    doc_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int


class ApiConfigCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., min_length=1, max_length=500)
    api_key: str = Field(..., min_length=1, max_length=500)
    model_name: str = Field(..., min_length=1, max_length=200)


class ApiConfigRead(BaseModel):
    id: int
    display_name: str
    provider: str
    base_url: str
    api_key: str
    model_name: str
    is_preset: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None


class ErpConfigCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., min_length=1, max_length=500)
    auth_type: str = "none"
    token_url: Optional[str] = None
    token_header: Optional[str] = None
    credential_key: Optional[str] = None
    credential_secret: Optional[str] = None
    static_token: Optional[str] = None
    tenant_id: Optional[str] = None


class ErpConfigRead(BaseModel):
    id: int
    display_name: str
    provider: str
    base_url: str
    auth_type: str
    token_url: Optional[str]
    token_header: Optional[str]
    credential_key: Optional[str]
    credential_secret: Optional[str]
    static_token: Optional[str]
    tenant_id: Optional[str]
    is_preset: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ErpConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    auth_type: Optional[str] = None
    token_url: Optional[str] = None
    token_header: Optional[str] = None
    credential_key: Optional[str] = None
    credential_secret: Optional[str] = None
    static_token: Optional[str] = None
    tenant_id: Optional[str] = None
