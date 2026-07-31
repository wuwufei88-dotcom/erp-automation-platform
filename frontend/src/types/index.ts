export type ProjectStatus =
  | "new"
  | "demand_parse"
  | "solution_generate"
  | "system_config"
  | "data_migration"
  | "ops_qa"
  | "completed"
  | "failed";

export type AgentType =
  | "demand_parser"
  | "solution_generator"
  | "system_config"
  | "data_migration"
  | "ops_qa";

export type AgentStatus = "pending" | "running" | "completed" | "failed" | "skipped";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  api_config_id: number | null;
  erp_config_id: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ProjectDetail extends Project {
  agents: Agent[];
}

export interface Agent {
  id: string;
  agent_type: AgentType;
  status: AgentStatus;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
  error_message: string | null;
  result_json?: Record<string, unknown> | null;
}

export interface AgentExecution {
  id: string;
  attempt_number: number;
  status: "running" | "completed" | "failed";
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface AgentLog {
  id: number;
  level: "info" | "warning" | "error" | "debug";
  message: string;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  mime_type: string | null;
  size_bytes: number | null;
  doc_type: string;
  uploaded_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const AGENT_LABELS: Record<AgentType, string> = {
  demand_parser: "需求解析",
  solution_generator: "方案生成",
  system_config: "系统配置",
  data_migration: "数据迁移",
  ops_qa: "运维答疑",
};

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  new: "新建",
  demand_parse: "需求解析中",
  solution_generate: "方案生成中",
  system_config: "系统配置中",
  data_migration: "数据迁移中",
  ops_qa: "运维答疑中",
  completed: "已完成",
  failed: "失败",
};

export interface ApiConfig {
  id: number;
  display_name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model_name: string;
  is_preset: number;
  created_at: string;
}

export interface ErpConfig {
  id: number;
  display_name: string;
  provider: string;
  base_url: string;
  auth_type: string;
  token_url: string | null;
  token_header: string | null;
  credential_key: string | null;
  credential_secret: string | null;
  static_token: string | null;
  tenant_id: string | null;
  is_preset: number;
  created_at: string;
}
