import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { listProjects, createProject, deleteProject } from "../services/projects";
import { listApiConfigs } from "../services/apiConfigs";
import { listErpConfigs } from "../services/erpConfigs";
import { colors } from "../tokens/colors";
import { spacing } from "../tokens/spacing";
import { rounded } from "../tokens/rounded";
import { STATUS_LABELS, type Project, type ProjectStatus } from "../types";
import Button from "../components/ui/Button";
import Badge from "../components/ui/Badge";
import TextInput from "../components/ui/TextInput";
import ConfirmModal from "../components/ui/ConfirmModal";
import Container from "../components/layout/Container";

const statusColor = (status: ProjectStatus): string => {
  if (status === "completed") return colors.success;
  if (status === "failed") return colors.error;
  if (status === "new") return colors.muted;
  return colors.brandAccent;
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedApiConfigId, setSelectedApiConfigId] = useState<number | undefined>(undefined);
  const [selectedErpConfigId, setSelectedErpConfigId] = useState<number | undefined>(undefined);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchMode, setBatchMode] = useState(false);
  const [isNarrow, setIsNarrow] = useState(window.innerWidth < 768);
  useEffect(() => {
    const onResize = () => setIsNarrow(window.innerWidth < 768);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState<{ show: boolean; title: string; message: string; onConfirm: () => void }>({ show: false, title: "", message: "", onConfirm: () => {} });

  const { data, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: () => listProjects({ page: 1, size: 20 }),
    refetchInterval: 10000,
  });

  const { data: apiConfigs } = useQuery({
    queryKey: ["api-configs"],
    queryFn: listApiConfigs,
  });

  const { data: erpConfigs } = useQuery({
    queryKey: ["erp-configs"],
    queryFn: listErpConfigs,
  });

  // Grey-out dialog state
  const [greyDialog, setGreyDialog] = useState<{ show: boolean; optionName: string; optionType: "api" | "erp" }>({ show: false, optionName: "", optionType: "api" });

  // Helper: check if an ERP config has valid credentials
  const erpIsConfigured = (c: { auth_type: string; credential_key?: string | null; credential_secret?: string | null; static_token?: string | null }) => {
    if (c.auth_type === "none") return true;
    if (c.auth_type === "static_token") return !!c.static_token;
    return !!(c.credential_key && c.credential_secret);
  };

  const createMutation = useMutation({
    mutationFn: () => createProject({ name: name.trim(), description: description.trim() || undefined, api_config_id: selectedApiConfigId, erp_config_id: selectedErpConfigId }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowCreate(false);
      setName("");
      setDescription("");
      setSelectedApiConfigId(undefined);
      setSelectedErpConfigId(undefined);
      navigate(`/projects/${project.id}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProject(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      // Clean up localStorage for this project
      localStorage.removeItem(`stream_${id}`);
      localStorage.removeItem(`output_${id}`);
    },
  });

  const batchDeleteMutation = useMutation({
    mutationFn: async (ids: string[]) => { await Promise.all(ids.map((id) => deleteProject(id))); },
    onSuccess: (_data, ids) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      ids.forEach((id: string) => { localStorage.removeItem(`stream_${id}`); localStorage.removeItem(`output_${id}`); });
      setSelectedIds(new Set());
      setBatchMode(false);
    },
  });

  const stats = {
    total: data?.total ?? 0,
    running: data?.items.filter((p: Project) => !["completed", "failed", "new"].includes(p.status)).length ?? 0,
    completed: data?.items.filter((p: Project) => p.status === "completed").length ?? 0,
    failed: data?.items.filter((p: Project) => p.status === "failed").length ?? 0,
  };

  return (
    <Container>
      <div style={{ padding: `${spacing.xxl}px 0` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.xl }}>
          <h1
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 36,
              fontWeight: 600,
              lineHeight: 1.15,
              letterSpacing: "-1px",
              color: colors.ink,
            }}
          >
            交付项目
          </h1>
          <div style={{ display: "flex", gap: spacing.sm }}>
            {batchMode ? (
              <>
                <div
                  onClick={() => { setBatchMode(false); setSelectedIds(new Set()); }}
                  style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.muted, cursor: "pointer", padding: "10px 16px", borderRadius: rounded.md, border: `1px solid ${colors.hairline}`, transition: "all 0.15s", display: "flex", alignItems: "center" }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = colors.ink; e.currentTarget.style.borderColor = colors.ink; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = colors.muted; e.currentTarget.style.borderColor = colors.hairline; }}
                >
                  取消
                </div>
                {selectedIds.size > 0 && (
                  <div
                    onClick={() => setConfirmDialog({ show: true, title: "确认删除", message: `确定删除选中的 ${selectedIds.size} 个项目？此操作不可撤销。`, onConfirm: () => batchDeleteMutation.mutate(Array.from(selectedIds)) })}
                    style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.error, cursor: "pointer", padding: "10px 16px", borderRadius: rounded.md, border: `1px solid ${colors.error}`, transition: "all 0.15s", display: "flex", alignItems: "center" }}
                    onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = colors.error; e.currentTarget.style.color = colors.onPrimary; }}
                    onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent"; e.currentTarget.style.color = colors.error; }}
                  >
                    删除选中 ({selectedIds.size})
                  </div>
                )}
              </>
            ) : (
              <div
                onClick={() => setBatchMode(true)}
                style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.muted, cursor: "pointer", padding: "10px 16px", borderRadius: rounded.md, border: `1px solid ${colors.hairline}`, transition: "all 0.15s", display: "flex", alignItems: "center" }}
                onMouseEnter={(e) => { e.currentTarget.style.color = colors.ink; e.currentTarget.style.borderColor = colors.ink; }}
                onMouseLeave={(e) => { e.currentTarget.style.color = colors.muted; e.currentTarget.style.borderColor = colors.hairline; }}
              >
                批量操作
              </div>
            )}
            <Button variant="primary" onClick={() => setShowCreate(true)}>
              新建项目
            </Button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: isNarrow ? "repeat(2, 1fr)" : "repeat(4, 1fr)", gap: spacing.lg, marginBottom: spacing.xl }}>
          {[
            { label: "全部项目", value: stats.total },
            { label: "运行中", value: stats.running },
            { label: "已完成", value: stats.completed },
            { label: "失败", value: stats.failed },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                backgroundColor: colors.surfaceCard,
                borderRadius: rounded.lg,
                padding: spacing.lg,
              }}
            >
              <div style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.muted, marginBottom: spacing.xs }}>
                {s.label}
              </div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, color: colors.ink }}>
                {s.value}
              </div>
            </div>
          ))}
        </div>

        {isLoading ? (
          <p style={{ color: colors.muted }}>加载中...</p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: isNarrow ? "repeat(1, 1fr)" : "repeat(3, 1fr)", gap: spacing.lg }}>
            {(data?.items ?? []).map((project: Project) => (
              <div
                key={project.id}
                onClick={() => {
                  if (batchMode) {
                    setSelectedIds((prev) => {
                      const next = new Set(prev);
                      prev.has(project.id) ? next.delete(project.id) : next.add(project.id);
                      return next;
                    });
                  } else {
                    navigate(`/projects/${project.id}`);
                  }
                }}
                style={{
                  backgroundColor: colors.canvas,
                  borderRadius: rounded.lg,
                  border: `1px solid ${selectedIds.has(project.id) ? colors.ink : colors.hairline}`,
                  padding: spacing.lg,
                  cursor: batchMode ? "pointer" : "pointer",
                  transition: "box-shadow 0.15s, border-color 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)")}
                onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: spacing.sm }}>
                  <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                    {batchMode && (
                    <input
                      type="checkbox"
                      checked={selectedIds.has(project.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        setSelectedIds((prev) => {
                          const next = new Set(prev);
                          e.target.checked ? next.add(project.id) : next.delete(project.id);
                          return next;
                        });
                      }}
                      onClick={(e) => e.stopPropagation()}
                      style={{ cursor: "pointer", width: 16, height: 16, accentColor: colors.ink }}
                    />
                    )}
                    <h3 style={{ fontFamily: "var(--font-body)", fontSize: 16, fontWeight: 600, color: colors.ink }}>
                      {project.name}
                    </h3>
                  </div>
                  <Badge background={statusColor(project.status as ProjectStatus)} color={colors.onPrimary}>
                    {STATUS_LABELS[project.status as ProjectStatus]}
                  </Badge>
                </div>
                {project.description && (
                  <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted, marginBottom: spacing.md }}>
                    {project.description}
                  </p>
                )}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontFamily: "var(--font-body)", fontSize: 13, color: colors.mutedSoft }}>
                    {new Date(project.created_at).toLocaleDateString("zh-CN")}
                  </div>
                  <div
                    onClick={(e) => { e.stopPropagation(); setConfirmDialog({ show: true, title: "确认删除", message: `确定删除项目「${project.name}」？此操作不可撤销。`, onConfirm: () => deleteMutation.mutate(project.id) }); }}
                    style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.mutedSoft, cursor: "pointer", padding: "4px 8px", borderRadius: rounded.sm, transition: "all 0.15s" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = colors.error; e.currentTarget.style.backgroundColor = "#fef2f2"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = colors.mutedSoft; e.currentTarget.style.backgroundColor = "transparent"; }}
                  >
                    删除
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {showCreate && (
          <div
            style={{
              position: "fixed",
              inset: 0,
              backgroundColor: "rgba(0,0,0,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 200,
            }}
            onClick={() => setShowCreate(false)}
          >
            <div
              style={{
                backgroundColor: colors.canvas,
                borderRadius: rounded.lg,
                padding: spacing.xl,
                width: 480,
                maxWidth: "90vw",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <h2 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, color: colors.ink, marginBottom: spacing.lg }}>
                新建交付项目
              </h2>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted, marginBottom: spacing.lg }}>
                创建项目后，你需要上传需求文档并手动启动 Agent 工作流。
              </p>
              <TextInput
                label="项目名称"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="例如：某某公司 ERP 实施项目"
                style={{ marginBottom: spacing.md }}
              />
              <div style={{ marginBottom: spacing.lg }}>
                <TextInput
                  label="项目描述（选填）"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="简要描述项目背景和目标"
                />
              </div>
              <div style={{ marginBottom: spacing.lg }}>
                <label style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.ink, display: "block", marginBottom: 4 }}>
                  API 配置（可选）
                </label>
                <select
                  value={selectedApiConfigId ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (!val) { setSelectedApiConfigId(undefined); return; }
                    const c = (apiConfigs ?? []).find((ac) => ac.id === Number(val));
                    if (c && (!c.api_key || c.api_key.trim() === "")) {
                      setGreyDialog({ show: true, optionName: `#${c.id} ${c.display_name}`, optionType: "api" });
                      setSelectedApiConfigId(undefined);
                      return;
                    }
                    setSelectedApiConfigId(Number(val));
                  }}
                  style={{
                    width: "100%", height: 40, padding: "8px 12px",
                    fontFamily: "var(--font-body)", fontSize: 14,
                    border: `1px solid ${colors.hairline}`, borderRadius: rounded.md,
                    backgroundColor: colors.canvas, color: colors.ink,
                    cursor: "pointer",
                    transition: "border-color 0.15s, box-shadow 0.15s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = colors.ink; e.currentTarget.style.boxShadow = "0 0 0 1px rgba(0,0,0,0.1)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = colors.hairline; e.currentTarget.style.boxShadow = "none"; }}
                >
                  <option value="">使用默认配置</option>
                  {(apiConfigs ?? []).map((c) => {
                    const configured = c.api_key && c.api_key.trim() !== "";
                    return (
                      <option
                        key={c.id}
                        value={c.id}
                        style={{
                          color: configured ? colors.ink : colors.mutedSoft,
                          fontStyle: configured ? "normal" : "italic",
                        }}
                      >
                        #{c.id} {c.display_name} ({c.provider}){configured ? "" : " — 需配置"}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div style={{ marginBottom: spacing.lg }}>
                <label style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.ink, display: "block", marginBottom: 4 }}>
                  ERP 系统（可选）
                </label>
                <select
                  value={selectedErpConfigId ?? ""}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (!val) { setSelectedErpConfigId(undefined); return; }
                    const c = (erpConfigs ?? []).find((ec) => ec.id === Number(val));
                    if (c && !erpIsConfigured(c)) {
                      setGreyDialog({ show: true, optionName: `#${c.id} ${c.display_name}`, optionType: "erp" });
                      setSelectedErpConfigId(undefined);
                      return;
                    }
                    setSelectedErpConfigId(Number(val));
                  }}
                  style={{
                    width: "100%", height: 40, padding: "8px 12px",
                    fontFamily: "var(--font-body)", fontSize: 14,
                    border: `1px solid ${colors.hairline}`, borderRadius: rounded.md,
                    backgroundColor: colors.canvas, color: colors.ink,
                    cursor: "pointer",
                    transition: "border-color 0.15s, box-shadow 0.15s",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = colors.ink; e.currentTarget.style.boxShadow = "0 0 0 1px rgba(0,0,0,0.1)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = colors.hairline; e.currentTarget.style.boxShadow = "none"; }}
                >
                  <option value="">不使用 ERP 系统</option>
                  {(erpConfigs ?? []).map((c) => {
                    const configured = erpIsConfigured(c);
                    return (
                      <option
                        key={c.id}
                        value={c.id}
                        style={{
                          color: configured ? colors.ink : colors.mutedSoft,
                          fontStyle: configured ? "normal" : "italic",
                        }}
                      >
                        #{c.id} {c.display_name}{c.tenant_id ? ` [租户#${c.tenant_id}]` : ""} ({c.provider}){configured ? "" : " — 需配置"}
                      </option>
                    );
                  })}
                </select>
              </div>
              <div style={{ display: "flex", gap: spacing.sm, justifyContent: "flex-end" }}>
                <Button variant="secondary" onClick={() => setShowCreate(false)}>
                  取消
                </Button>
                <Button
                  variant="primary"
                  disabled={!name.trim() || createMutation.isPending}
                  onClick={() => createMutation.mutate()}
                >
                  {createMutation.isPending ? "创建中..." : "创建项目"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Grey-out dialog for unconfigured options */}
        {greyDialog.show && (
          <div
            style={{
              position: "fixed", inset: 0,
              backgroundColor: "rgba(0,0,0,0.3)",
              display: "flex", alignItems: "center", justifyContent: "center",
              zIndex: 300,
            }}
            onClick={() => setGreyDialog({ show: false, optionName: "", optionType: "api" })}
          >
            <div
              style={{
                backgroundColor: colors.canvas, borderRadius: rounded.lg,
                padding: spacing.xl, width: 420, maxWidth: "90vw",
                textAlign: "center",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 600, color: colors.ink, marginBottom: spacing.sm }}>
                此选项需要在 API 管理页面中配置
              </div>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted, marginBottom: spacing.xl }}>
                「{greyDialog.optionName}」尚未配置{greyDialog.optionType === "api" ? " API Key" : "凭证"}，无法在项目中使用。
              </p>
              <div style={{ display: "flex", gap: spacing.sm, justifyContent: "center" }}>
                <Button
                  variant="secondary"
                  onClick={() => setGreyDialog({ show: false, optionName: "", optionType: "api" })}
                >
                  取消
                </Button>
                <Button
                  variant="primary"
                  onClick={() => { setGreyDialog({ show: false, optionName: "", optionType: "api" }); navigate("/settings/api"); }}
                >
                  前往配置
                </Button>
              </div>
            </div>
          </div>
        )}

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
