import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listApiConfigs, createApiConfig, updateApiConfig, deleteApiConfig, seedPresets } from "../services/apiConfigs";
import { listErpConfigs, createErpConfig, updateErpConfig, deleteErpConfig, seedErpPresetsForce, resetErpPreset, listErpProviders, type ErpProvider } from "../services/erpConfigs";
import { colors } from "../tokens/colors";
import { spacing } from "../tokens/spacing";
import { rounded } from "../tokens/rounded";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import TextInput from "../components/ui/TextInput";
import ConfirmModal from "../components/ui/ConfirmModal";
import Container from "../components/layout/Container";
import type { ApiConfig, ErpConfig } from "../types";

const PROVIDER_OPTIONS = [
  { value: "OpenAI", label: "OpenAI", base: "https://api.openai.com/v1" },
  { value: "Anthropic", label: "Anthropic", base: "https://api.anthropic.com" },
  { value: "DeepSeek", label: "DeepSeek", base: "https://api.deepseek.com/v1" },
  { value: "OpenRouter", label: "OpenRouter", base: "https://openrouter.ai/api/v1" },
  { value: "Groq", label: "Groq", base: "https://api.groq.com/openai/v1" },
  { value: "Mistral", label: "Mistral", base: "https://api.mistral.ai/v1" },
  { value: "SiliconFlow", label: "硅基流动", base: "https://api.siliconflow.cn/v1" },
  { value: "Alibaba", label: "阿里百炼", base: "https://dashscope.aliyuncs.com/compatible-mode/v1" },
  { value: "Moonshot", label: "Moonshot/Kimi", base: "https://api.moonshot.cn/v1" },
  { value: "Ollama", label: "Ollama (本地)", base: "http://localhost:11434/v1" },
  { value: "vLLM", label: "vLLM (本地)", base: "http://localhost:8000/v1" },
  { value: "Custom", label: "自定义", base: "" },
];

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ display_name: "", provider: "", base_url: "", api_key: "", model_name: "" });
  const [showAdd, setShowAdd] = useState(false);

  const { data: configs, isLoading } = useQuery({
    queryKey: ["api-configs"],
    queryFn: listApiConfigs,
  });

  const createMutation = useMutation({
    mutationFn: createApiConfig,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["api-configs"] }); resetForm(); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ApiConfig> }) => updateApiConfig(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["api-configs"] }); resetForm(); },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteApiConfig,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-configs"] }),
  });

  const seedMutation = useMutation({
    mutationFn: seedPresets,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-configs"] }),
  });

  // ─── ERP Config State ───
  const [erpEditingId, setErpEditingId] = useState<number | null>(null);
  const [erpForm, setErpForm] = useState({ display_name: "", provider: "", base_url: "", auth_type: "none", token_url: "", token_header: "", credential_key: "", credential_secret: "", static_token: "", tenant_id: "" });
  const [showErpAdd, setShowErpAdd] = useState(false);

  const { data: erpConfigs } = useQuery({ queryKey: ["erp-configs"], queryFn: listErpConfigs });

  const erpCreateMutation = useMutation({
    mutationFn: createErpConfig, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["erp-configs"] }); resetErpForm(); },
  });
  const erpUpdateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ErpConfig> }) => updateErpConfig(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["erp-configs"] }); resetErpForm(); },
  });
  const erpDeleteMutation = useMutation({
    mutationFn: deleteErpConfig, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["erp-configs"] }),
  });
  const erpSeedMutation = useMutation({
    mutationFn: seedErpPresetsForce,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["erp-configs"] }),
  });

  const erpResetMutation = useMutation({
    mutationFn: resetErpPreset,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["erp-configs"] }),
  });

  const resetErpForm = () => { setErpForm({ display_name: "", provider: "", base_url: "", auth_type: "none", token_url: "", token_header: "", credential_key: "", credential_secret: "", static_token: "", tenant_id: "" }); setErpEditingId(null); setShowErpAdd(false); };
  const startErpEdit = (c: ErpConfig) => { setErpForm({ display_name: c.display_name, provider: c.provider, base_url: c.base_url, auth_type: c.auth_type, token_url: c.token_url || "", token_header: c.token_header || "", credential_key: c.credential_key || "", credential_secret: c.credential_secret || "", static_token: c.static_token || "", tenant_id: c.tenant_id || "" }); setErpEditingId(c.id); setShowErpAdd(true); };

  const AUTH_TYPES = [
    { value: "none", label: "无认证" },
    { value: "static_token", label: "固定 Token" },
    { value: "oauth2_password", label: "OAuth2 密码模式" },
    { value: "oauth2_client", label: "OAuth2 客户端模式" },
    { value: "api_key", label: "API Key（Bearer Token）" },
    { value: "basic", label: "HTTP Basic Auth" },
  ];

  // ERP providers from YAML configs
  const { data: erpProviders } = useQuery({ queryKey: ["erp-providers"], queryFn: listErpProviders, staleTime: 60000 });

  const resetForm = () => {
    setForm({ display_name: "", provider: "", base_url: "", api_key: "", model_name: "" });
    setEditingId(null);
    setShowAdd(false);
  };

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState<{ show: boolean; title: string; message: string; onConfirm: () => void }>({ show: false, title: "", message: "", onConfirm: () => {} });

  const startEdit = (c: ApiConfig) => {
    setForm({ display_name: c.display_name, provider: c.provider, base_url: c.base_url, api_key: c.api_key, model_name: c.model_name });
    setEditingId(c.id);
    setShowAdd(true);
  };

  const handleProviderChange = (provider: string) => {
    const preset = PROVIDER_OPTIONS.find((p) => p.value === provider);
    setForm({ ...form, provider, base_url: preset?.base || "" });
  };

  const handleSubmit = () => {
    if (editingId != null) {
      updateMutation.mutate({ id: editingId, data: form });
    } else {
      createMutation.mutate(form);
    }
  };

  const maskKey = (key: string) => {
    if (!key) return "(未设置)";
    if (key.length <= 8) return "***";
    return key.slice(0, 4) + "****" + key.slice(-4);
  };

  return (
    <Container>
      <div style={{ padding: `${spacing.xxl}px 0` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.xl }}>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 600, lineHeight: 1.15, letterSpacing: "-1px", color: colors.ink }}>
            API 管理
          </h1>
          <div style={{ display: "flex", gap: spacing.sm }}>
            <Button variant="secondary" onClick={() => seedMutation.mutate()} disabled={seedMutation.isPending}>
              初始化预置提供商
            </Button>
            <Button variant="primary" onClick={() => setShowAdd(true)}>
              添加配置
            </Button>
          </div>
        </div>

        {isLoading ? (
          <p style={{ color: colors.muted }}>加载中...</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
            {(configs ?? []).map((c) => (
              <div
                key={c.id}
                style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  backgroundColor: colors.canvas, borderRadius: rounded.lg,
                  border: `1px solid ${colors.hairline}`, padding: `${spacing.md}px ${spacing.lg}px`,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: spacing.lg, flex: 1 }}>
                  <span style={{ fontFamily: "var(--font-code)", fontSize: 14, color: colors.muted, minWidth: 30 }}>
                    #{c.id}
                  </span>
                  <div style={{ minWidth: 160 }}>
                    <div style={{ fontFamily: "var(--font-body)", fontSize: 16, fontWeight: 600, color: colors.ink }}>
                      {c.display_name}
                    </div>
                    <div style={{ fontFamily: "var(--font-body)", fontSize: 13, color: colors.muted }}>
                      {c.model_name}
                    </div>
                  </div>
                  <Badge background={c.is_preset ? colors.badgeViolet : colors.surfaceCard} color={c.is_preset ? colors.onPrimary : colors.muted}>
                    {c.provider}
                  </Badge>
                  <span style={{ fontFamily: "var(--font-code)", fontSize: 13, color: colors.mutedSoft }}>
                    {c.base_url}
                  </span>
                  <span style={{ fontFamily: "var(--font-code)", fontSize: 13, color: colors.mutedSoft }}>
                    {maskKey(c.api_key)}
                  </span>
                </div>
                <div style={{ display: "flex", gap: spacing.xs }}>
                  {c.is_preset === 0 && (
                    <>
                      <Button variant="text-link" onClick={() => startEdit(c)}>编辑</Button>
                      <Button variant="text-link" onClick={() => setConfirmDialog({ show: true, title: "确认删除", message: "确定删除此 API 配置？", onConfirm: () => deleteMutation.mutate(c.id) })}>
                        删除
                      </Button>
                    </>
                  )}
                  {c.is_preset === 1 && (
                    <Button variant="text-link" onClick={() => startEdit(c)}>填入 Key</Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {showAdd && (
          <div style={{ position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200 }}
            onClick={resetForm}>
            <div style={{ backgroundColor: colors.canvas, borderRadius: rounded.lg, padding: spacing.xl, width: 520, maxWidth: "90vw" }}
              onClick={(e) => e.stopPropagation()}>
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, color: colors.ink, marginBottom: spacing.lg }}>
                {editingId != null ? "编辑 API 配置" : "添加 API 配置"}
              </h2>

              <div style={{ marginBottom: spacing.md }}>
                <label style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.ink, display: "block", marginBottom: 4 }}>
                  提供商
                </label>
                <select
                  value={form.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  style={{
                    width: "100%", height: 40, padding: "8px 12px",
                    fontFamily: "var(--font-body)", fontSize: 14,
                    border: `1px solid ${colors.hairline}`, borderRadius: rounded.md,
                    backgroundColor: colors.canvas, color: colors.ink,
                  }}
                >
                  <option value="">选择提供商...</option>
                  {PROVIDER_OPTIONS.map((p) => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>

              <TextInput label="显示名称" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} placeholder="例如：公司 DeepSeek 账号" style={{ marginBottom: spacing.md }} />
              <TextInput label="Base URL" value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} placeholder="https://api.deepseek.com/v1" style={{ marginBottom: spacing.md }} />
              <TextInput label="API Key" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} placeholder="sk-..." style={{ marginBottom: spacing.md }} />
              <TextInput label="模型名称" value={form.model_name} onChange={(e) => setForm({ ...form, model_name: e.target.value })} placeholder="deepseek-chat" style={{ marginBottom: spacing.lg }} />

              <div style={{ display: "flex", gap: spacing.sm, justifyContent: "flex-end" }}>
                <Button variant="secondary" onClick={resetForm}>取消</Button>
                <Button variant="primary" onClick={handleSubmit}
                  disabled={!form.display_name || !form.provider || !form.base_url || !form.model_name}>
                  {editingId != null ? "保存" : "添加"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ─── ERP Config Section ─── */}
        <div style={{ marginTop: spacing.section }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.lg }}>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, color: colors.ink }}>
              ERP 连接配置
            </h2>
            <div style={{ display: "flex", gap: spacing.sm }}>
              <Button
                variant="secondary"
                onClick={() => setConfirmDialog({
                  show: true, title: "初始化全部 ERP 配置",
                  message: "将删除全部现有 ERP 配置（包括自定义配置），并从 YAML 文件中重新加载 JEECG、Odoo、ERPNext、金蝶、SAP、Dynamics 365、用友 YonSuite 共 7 个 ERP 系统的默认预设。确定继续？",
                  onConfirm: () => erpSeedMutation.mutate(),
                })}
                disabled={erpSeedMutation.isPending}
              >
                初始化全部 ERP 配置
              </Button>
              <Button variant="primary" onClick={() => setShowErpAdd(true)}>
                添加 ERP
              </Button>
            </div>
          </div>

          <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted, marginBottom: spacing.lg }}>
            配置目标 ERP 系统的连接参数（Base URL + 认证方式）。创建项目时选择对应的 ERP 配置，Agent 将自动连接并执行操作。
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
            {(erpConfigs ?? []).map((c) => (
              <div key={c.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", backgroundColor: colors.canvas, borderRadius: rounded.lg, border: `1px solid ${colors.hairline}`, padding: `${spacing.md}px ${spacing.lg}px` }}>
                <div style={{ display: "flex", alignItems: "center", gap: spacing.lg, flex: 1 }}>
                  <span style={{ fontFamily: "var(--font-code)", fontSize: 14, color: colors.muted, minWidth: 24 }}>#{c.id}</span>
                  <div style={{ minWidth: 140 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontFamily: "var(--font-body)", fontSize: 16, fontWeight: 600, color: colors.ink }}>{c.display_name}</span>
                      {c.tenant_id && (
                        <span style={{ fontFamily: "var(--font-code)", fontSize: 11, color: colors.brandAccent, backgroundColor: "#eef2ff", padding: "1px 6px", borderRadius: rounded.sm }}>
                          租户 #{c.tenant_id}
                        </span>
                      )}
                    </div>
                    <div style={{ fontFamily: "var(--font-code)", fontSize: 12, color: colors.mutedSoft }}>{c.base_url}</div>
                  </div>
                  <Badge background={c.is_preset ? colors.badgeViolet : colors.surfaceCard} color={c.is_preset ? colors.onPrimary : colors.muted}>{c.provider}</Badge>
                  <Badge background={colors.surfaceCard} color={colors.muted}>{AUTH_TYPES.find(t => t.value === c.auth_type)?.label || c.auth_type}</Badge>
                  <span style={{ fontFamily: "var(--font-code)", fontSize: 12, color: colors.mutedSoft }}>
                    {c.auth_type !== "none" ? (c.static_token ? "Token已设置" : c.credential_key ? "凭证已设" : "需配置凭证") : "无需认证"}
                  </span>
                </div>
                <div style={{ display: "flex", gap: spacing.xs }}>
                  {c.is_preset === 0 && (
                    <>
                      <Button variant="text-link" onClick={() => startErpEdit(c)}>编辑</Button>
                      <Button variant="text-link" onClick={() => setConfirmDialog({ show: true, title: "确认删除", message: "确定删除此 ERP 配置？已交付的项目将无法使用此配置。", onConfirm: () => erpDeleteMutation.mutate(c.id) })}>删除</Button>
                    </>
                  )}
                  {c.is_preset === 1 && (
                    <>
                      <Button
                        variant="text-link"
                        onClick={() => setConfirmDialog({
                          show: true, title: "初始化配置",
                          message: `将「${c.display_name}」重置为 YAML 文件中定义的默认配置。已填写的凭证（用户名/密码等）将被清除。确定继续？`,
                          onConfirm: () => erpResetMutation.mutate(c.id),
                        })}
                      >
                        初始化
                      </Button>
                      <Button variant="text-link" onClick={() => startErpEdit(c)}>配置凭证</Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>

          {showErpAdd && (
            <div style={{ position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200 }} onClick={resetErpForm}>
              <div style={{ backgroundColor: colors.canvas, borderRadius: rounded.lg, padding: spacing.xl, width: 560, maxWidth: "90vw", maxHeight: "90vh", overflow: "auto" }} onClick={(e) => e.stopPropagation()}>
                <h2 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, color: colors.ink, marginBottom: spacing.lg }}>
                  {erpEditingId != null ? "编辑 ERP 配置" : "添加 ERP 配置"}
                </h2>

                <TextInput label="显示名称" value={erpForm.display_name} onChange={(e) => setErpForm({ ...erpForm, display_name: e.target.value })} placeholder="例如：公司 YonSuite 生产环境" style={{ marginBottom: spacing.md }} />

                <div style={{ marginBottom: spacing.md }}>
                  <label style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.ink, display: "block", marginBottom: 4 }}>
                    提供商
                  </label>
                  <select
                    value={erpForm.provider}
                    onChange={(e) => {
                      const prov = (erpProviders ?? []).find((p: ErpProvider) => p.provider === e.target.value);
                      if (prov) {
                        setErpForm({
                          ...erpForm,
                          provider: prov.provider,
                          display_name: erpForm.display_name || prov.name,
                          auth_type: prov.auth_type,
                          base_url: erpForm.base_url || prov.default_base_url,
                          token_url: prov.token_url,
                          token_header: prov.token_header,
                        });
                      } else {
                        setErpForm({ ...erpForm, provider: e.target.value });
                      }
                    }}
                    style={{
                      width: "100%", height: 40, padding: "8px 12px",
                      fontFamily: "var(--font-body)", fontSize: 14,
                      border: `1px solid ${colors.hairline}`, borderRadius: rounded.md,
                      backgroundColor: colors.canvas, color: colors.ink,
                    }}
                  >
                    <option value="">选择 ERP 系统...</option>
                    {(erpProviders ?? []).map((p: ErpProvider) => (
                      <option key={p.provider} value={p.provider}>{p.name}</option>
                    ))}
                    <option value="__custom__">自定义...</option>
                  </select>
                </div>

                <TextInput label="Base URL" value={erpForm.base_url} onChange={(e) => setErpForm({ ...erpForm, base_url: e.target.value })} placeholder="http://localhost:8080/jeecg-boot" style={{ marginBottom: spacing.md }} />

                <div style={{ marginBottom: spacing.md }}>
                  <label style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.ink, display: "block", marginBottom: 4 }}>认证方式</label>
                  <select value={erpForm.auth_type} onChange={(e) => setErpForm({ ...erpForm, auth_type: e.target.value })}
                    style={{ width: "100%", height: 40, padding: "8px 12px", fontFamily: "var(--font-body)", fontSize: 14, border: `1px solid ${colors.hairline}`, borderRadius: rounded.md, backgroundColor: colors.canvas, color: colors.ink }}>
                    {AUTH_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>

                {erpForm.auth_type !== "none" && (
                  <>
                    <TextInput label="Token 端点路径" value={erpForm.token_url} onChange={(e) => setErpForm({ ...erpForm, token_url: e.target.value })} placeholder="/sys/login 或 /oauth2/token" style={{ marginBottom: spacing.md }} />
                    <TextInput label="Token Header" value={erpForm.token_header} onChange={(e) => setErpForm({ ...erpForm, token_header: e.target.value })} placeholder="X-Access-Token 或 Authorization: Bearer" style={{ marginBottom: spacing.md }} />
                    {erpForm.auth_type === "static_token" ? (
                      <TextInput label="固定 Token 值" value={erpForm.static_token} onChange={(e) => setErpForm({ ...erpForm, static_token: e.target.value })} placeholder="直接填写 Token 字符串" style={{ marginBottom: spacing.md }} />
                    ) : (
                      <>
                        <TextInput label="凭证 Key（用户名/AppKey/ClientId）" value={erpForm.credential_key} onChange={(e) => setErpForm({ ...erpForm, credential_key: e.target.value })} placeholder="admin 或 AppKey" style={{ marginBottom: spacing.md }} />
                        <TextInput label="凭证 Secret（密码/AppSecret/ClientSecret）" value={erpForm.credential_secret} onChange={(e) => setErpForm({ ...erpForm, credential_secret: e.target.value })} placeholder="密码或密钥" style={{ marginBottom: spacing.md }} />
                      </>
                    )}
                  </>
                )}

                <div style={{ marginBottom: spacing.lg }}>
                  <label style={{
                    fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500,
                    color: colors.ink, display: "flex", alignItems: "center", gap: 6,
                    marginBottom: 4,
                  }}>
                    租户 ID
                    <span
                      style={{
                        display: "inline-flex", alignItems: "center", justifyContent: "center",
                        width: 16, height: 16, borderRadius: "50%",
                        border: `1px solid ${colors.mutedSoft}`,
                        fontSize: 10, fontWeight: 600, color: colors.muted,
                        cursor: "help",
                        transition: "all 0.15s",
                      }}
                      title="多租户 ERP 中，租户（Tenant）代表一个独立的企业/组织单元。同一个 ERP 系统可以有多个租户，每个租户的数据完全隔离（组织架构、用户、权限等）。填写租户 ID 后，Agent 的所有操作将限定在该租户内。如需为不同客户创建多个租户，请在下方分别添加多条 ERP 配置，每条指定不同租户 ID。"
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = colors.ink; e.currentTarget.style.color = colors.canvas; e.currentTarget.style.borderColor = colors.ink; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; e.currentTarget.style.color = colors.muted; e.currentTarget.style.borderColor = colors.mutedSoft; }}
                    >
                      ?
                    </span>
                  </label>
                  <input
                    type="text"
                    value={erpForm.tenant_id}
                    onChange={(e) => setErpForm({ ...erpForm, tenant_id: e.target.value })}
                    placeholder="多租户 ERP 需要填写。同一 ERP 不同租户请分别添加多条配置"
                    style={{
                      width: "100%", height: 40, padding: "8px 12px",
                      fontFamily: "var(--font-body)", fontSize: 14,
                      border: `1px solid ${colors.hairline}`, borderRadius: rounded.md,
                      backgroundColor: colors.canvas, color: colors.ink,
                      boxSizing: "border-box",
                    }}
                  />
                </div>

                <div style={{ display: "flex", gap: spacing.sm, justifyContent: "flex-end" }}>
                  <Button variant="secondary" onClick={resetErpForm}>取消</Button>
                  <Button variant="primary" onClick={() => erpEditingId != null ? erpUpdateMutation.mutate({ id: erpEditingId, data: erpForm }) : erpCreateMutation.mutate(erpForm)}
                    disabled={!erpForm.display_name || !erpForm.provider || !erpForm.base_url}>
                    {erpEditingId != null ? "保存" : "添加"}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Styled Confirm Modal */}
        <ConfirmModal
          show={confirmDialog.show}
          title={confirmDialog.title}
          message={confirmDialog.message}
          variant="danger"
          onConfirm={() => { confirmDialog.onConfirm(); setConfirmDialog({ show: false, title: "", message: "", onConfirm: () => {} }); }}
          onCancel={() => setConfirmDialog({ show: false, title: "", message: "", onConfirm: () => {} })}
        />
      </div>
    </Container>
  );
}
