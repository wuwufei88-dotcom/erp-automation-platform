import api from "./api";
import type { ApiConfig } from "../types";

export async function listApiConfigs(): Promise<ApiConfig[]> {
  const res = await api.get<ApiConfig[]>("/admin/api-configs");
  return res.data;
}

export async function createApiConfig(data: {
  display_name: string;
  provider: string;
  base_url: string;
  api_key: string;
  model_name: string;
}): Promise<ApiConfig> {
  const res = await api.post<ApiConfig>("/admin/api-configs", data);
  return res.data;
}

export async function updateApiConfig(id: number, data: Partial<ApiConfig>): Promise<ApiConfig> {
  const res = await api.put<ApiConfig>(`/admin/api-configs/${id}`, data);
  return res.data;
}

export async function deleteApiConfig(id: number): Promise<void> {
  await api.delete(`/admin/api-configs/${id}`);
}

export async function seedPresets(): Promise<void> {
  await api.post("/admin/api-configs/seed-presets");
}
