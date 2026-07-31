import api from "./api";
import type { ErpConfig } from "../types";

export async function listErpConfigs(): Promise<ErpConfig[]> {
  const res = await api.get<ErpConfig[]>("/admin/erp-configs");
  return res.data;
}

export interface ErpProvider {
  provider: string;
  name: string;
  description: string;
  website: string;
  api_style: string;
  auth_type: string;
  token_url: string;
  token_header: string;
  credential_label: string;
  secret_label: string;
  default_base_url: string;
  source_file: string;
}

export async function listErpProviders(): Promise<ErpProvider[]> {
  const res = await api.get<ErpProvider[]>("/admin/erp-providers");
  return res.data;
}

export async function createErpConfig(data: Partial<ErpConfig>): Promise<ErpConfig> {
  const res = await api.post<ErpConfig>("/admin/erp-configs", data);
  return res.data;
}

export async function updateErpConfig(id: number, data: Partial<ErpConfig>): Promise<ErpConfig> {
  const res = await api.put<ErpConfig>(`/admin/erp-configs/${id}`, data);
  return res.data;
}

export async function deleteErpConfig(id: number): Promise<void> {
  await api.delete(`/admin/erp-configs/${id}`);
}

export async function seedErpPresets(): Promise<void> {
  await api.post("/admin/erp-configs/seed-presets");
}

export async function seedErpPresetsForce(): Promise<void> {
  await api.post("/admin/erp-configs/seed-presets?force=true");
}

export async function resetErpPreset(id: number): Promise<{ message: string; id: number }> {
  const res = await api.post<{ message: string; id: number }>(`/admin/erp-configs/${id}/reset`);
  return res.data;
}
