from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import DeclarativeBase, relationship

from app.database import engine


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(
            "new",
            "demand_parse",
            "solution_generate",
            "system_config",
            "data_migration",
            "ops_qa",
            "completed",
            "failed",
            name="project_status",
        ),
        default="new",
        nullable=False,
    )
    created_by = Column(String(36), nullable=True)
    api_config_id = Column(Integer, nullable=True)
    erp_config_id = Column(Integer, nullable=True)
    tenant_id = Column(String(50), nullable=True)  # JEECG tenant ID, per-project (not from ErpConfig)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    agents = relationship("ProjectAgent", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")


class ProjectAgent(Base):
    __tablename__ = "project_agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    agent_type = Column(
        Enum(
            "demand_parser",
            "solution_generator",
            "system_config",
            "data_migration",
            "ops_qa",
            name="agent_type",
        ),
        nullable=False,
    )
    status = Column(
        Enum("pending", "running", "completed", "failed", "skipped", name="agent_status"),
        default="pending",
        nullable=False,
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    result_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="agents")
    executions = relationship("AgentExecution", back_populates="project_agent", cascade="all, delete-orphan")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_agent_id = Column(String(36), ForeignKey("project_agents.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, default=1)
    status = Column(Enum("running", "completed", "failed", name="execution_status"), default="running", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    project_agent = relationship("ProjectAgent", back_populates="executions")
    logs = relationship("AgentLog", back_populates="execution", cascade="all, delete-orphan")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(36), ForeignKey("agent_executions.id", ondelete="CASCADE"), nullable=False)
    level = Column(Enum("info", "warning", "error", "debug", name="log_level"), default="info", nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("AgentExecution", back_populates="logs")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    minio_key = Column(String(1000), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    doc_type = Column(
        Enum(
            "requirement",
            "solution_ppt",
            "solution_excel",
            "migration_data",
            "error_report",
            name="doc_type",
        ),
        nullable=False,
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    milvus_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True)
    source_type = Column(Enum("manual", "faq", "error_pattern", "erp_manual", name="knowledge_source"), nullable=False)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApiConfig(Base):
    __tablename__ = "api_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=False)
    model_name = Column(String(200), nullable=False)
    is_preset = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ErpConfig(Base):
    __tablename__ = "erp_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    auth_type = Column(Enum("none", "static_token", "oauth2_password", "oauth2_client", "basic", "api_key", name="erp_auth_type"), default="none", nullable=False)
    token_url = Column(String(500), nullable=True)
    token_header = Column(String(100), nullable=True)
    credential_key = Column(String(500), nullable=True)
    credential_secret = Column(String(500), nullable=True)
    static_token = Column(String(500), nullable=True)
    tenant_id = Column(String(200), nullable=True)
    is_preset = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(Enum("admin", "operator", "viewer", name="user_role"), default="operator", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
