import api from "./api";
import type { Agent, AgentExecution, AgentLog } from "../types";

export async function listProjectAgents(projectId: string): Promise<Agent[]> {
  const res = await api.get<Agent[]>(`/projects/${projectId}/agents`);
  return res.data;
}

export async function getAgentOutput(projectId: string, agentType: string): Promise<unknown> {
  const res = await api.get(`/projects/${projectId}/agents/${agentType}/output`);
  return res.data;
}

export async function listAgentExecutions(projectId: string, agentType: string): Promise<AgentExecution[]> {
  const res = await api.get<AgentExecution[]>(`/projects/${projectId}/agents/${agentType}/executions`);
  return res.data;
}

export async function getExecutionLogs(projectId: string, executionId: string): Promise<AgentLog[]> {
  const res = await api.get<AgentLog[]>(`/projects/${projectId}/executions/${executionId}/logs`);
  return res.data;
}
