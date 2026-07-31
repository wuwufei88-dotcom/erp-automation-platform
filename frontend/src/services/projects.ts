import api from "./api";
import type { PaginatedResponse, Project, ProjectDetail } from "../types";

export async function createProject(data: { name: string; description?: string; api_config_id?: number; erp_config_id?: number }): Promise<Project> {
  const res = await api.post<Project>("/projects", data);
  return res.data;
}

export async function listProjects(params: {
  page?: number;
  size?: number;
  status?: string;
}): Promise<PaginatedResponse<Project>> {
  const res = await api.get("/projects", { params });
  return res.data;
}

export async function getProject(id: string): Promise<ProjectDetail> {
  const res = await api.get<ProjectDetail>(`/projects/${id}`);
  return res.data;
}

export async function triggerWorkflow(id: string): Promise<Project> {
  const res = await api.post<Project>(`/projects/${id}/trigger`);
  return res.data;
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/projects/${id}`);
}
