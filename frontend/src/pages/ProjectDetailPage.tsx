import { useState, useRef, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProject, triggerWorkflow } from "../services/projects";
import { listProjectAgents, getAgentOutput } from "../services/agents";
import { listApiConfigs } from "../services/apiConfigs";
import type { Document as DocInfo } from "../types";
import { colors } from "../tokens/colors";
import { spacing } from "../tokens/spacing";
import { rounded } from "../tokens/rounded";
import { STATUS_LABELS, type AgentStatus, type AgentType, type ProjectStatus } from "../types";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Container from "../components/layout/Container";

const A: AgentType[] = ["demand_parser", "solution_generator", "system_config", "data_migration", "ops_qa"];
const S = (s: AgentStatus) => {
  switch (s) { case "completed": return { bg: colors.success, t: "#fff", l: "已完成" }; case "running": return { bg: colors.brandAccent, t: "#fff", l: "运行中" }; case "failed": return { bg: colors.error, t: "#fff", l: "失败" }; default: return { bg: colors.surfaceCard, t: colors.muted, l: "等待中" }; }
};
const P = (s: ProjectStatus) => {
  if (s === "completed") return { bg: colors.success, text: colors.onPrimary }; if (s === "failed") return { bg: colors.error, text: colors.onPrimary }; if (s === "new") return { bg: colors.surfaceCard, text: colors.muted }; return { bg: colors.brandAccent, text: colors.onPrimary };
};
const I: Record<AgentType, { t: string; d: string }> = {
  demand_parser: { t: "需求解析", d: "解析客户需求文档，提取组织架构与模块清单" },
  solution_generator: { t: "方案生成", d: "生成实施方案、报价与培训课件" },
  system_config: { t: "系统配置", d: "自动配置 ERP 系统组织、审批流与基础档案" },
  data_migration: { t: "数据迁移", d: "清洗并导入客户历史业务数据" },
  ops_qa: { t: "运维答疑", d: "7×24 运维答疑与故障诊断" },
};
interface E { type: string; content?: unknown; name?: string; args?: Record<string, unknown>; result?: unknown; model?: string; tools?: string[]; }

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate(); const qc = useQueryClient();
  const fiRef = useRef<HTMLInputElement>(null);
  const logRef = useRef<Record<string, HTMLDivElement | null>>({});
  const autoRef = useRef<Record<string, boolean>>({});
  const esRef = useRef<EventSource | null>(null);
  const [sel, setSel] = useState<AgentType | null>(null);
  const [starting, setStarting] = useState(false);
  const [isNarrow, setIsNarrow] = useState(window.innerWidth < 768);
  // Responsive: track window width
  useEffect(() => {
    const onResize = () => setIsNarrow(window.innerWidth < 768);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const fileTsRef = useRef<Record<string, number>>({});
  const [ss, setSs] = useState<Record<string, { evts: E[]; conn: boolean; done: boolean; showH: boolean }>>(() => {
    try { return JSON.parse(localStorage.getItem(`stream_${id}`) || "{}"); } catch { return {}; }
  });
  const [out, setOut] = useState<Record<string, Record<string, unknown> | null>>(() => {
    try { return JSON.parse(localStorage.getItem(`output_${id}`) || "{}"); } catch { return {}; }
  });
  // Accumulated outputs across multiple runs (keyed by agentType_timestamp)
  const [outHistory, setOutHistory] = useState<{ key: string; agent: AgentType; data: Record<string, unknown>; ts: number }[]>(() => {
    try { return JSON.parse(localStorage.getItem(`outhist_${id}`) || "[]"); } catch { return []; }
  });

  // Persist stream state + output + history to localStorage
  useEffect(() => { try { localStorage.setItem(`stream_${id}`, JSON.stringify(ss)); } catch {} }, [ss, id]);
  useEffect(() => { try { localStorage.setItem(`output_${id}`, JSON.stringify(out)); } catch {} }, [out, id]);
  useEffect(() => { try { localStorage.setItem(`outhist_${id}`, JSON.stringify(outHistory)); } catch {} }, [outHistory, id]);

  const { data: pj } = useQuery({ queryKey: ["p", id], queryFn: () => getProject(id!), enabled: !!id, refetchInterval: 3000 });
  const { data: ags } = useQuery({ queryKey: ["a", id], queryFn: () => listProjectAgents(id!), enabled: !!id, refetchInterval: 3000 });
  const tm = useMutation({ mutationFn: () => triggerWorkflow(id!), onSuccess: () => { qc.invalidateQueries({ queryKey: ["p", id] }); qc.invalidateQueries({ queryKey: ["a", id] }); } });
  // Clear "starting" state once at least one agent is actually running
  useEffect(() => {
    if (starting && (ags ?? []).some(a => a.status !== "pending")) {
      setStarting(false);
    }
  }, [ags, starting]);
  const { data: acs } = useQuery({ queryKey: ["ac"], queryFn: listApiConfigs });
  const { data: docs } = useQuery({ queryKey: ["docs", id], queryFn: async () => { const r = await fetch(`/api/projects/${id}/documents`); return r.json() as Promise<DocInfo[]>; }, enabled: !!id });
  const abm = new Map((ags ?? []).map((a) => [a.agent_type, a]));
  const uploadedDocNames = (docs ?? []).map((d: DocInfo) => d.filename);

  // Auto-connect to stream when a running agent is detected (e.g. after page navigation)
  useEffect(() => {
    for (const at of A) {
      const a = abm.get(at);
      if (a?.status === "running" && !ss[at]?.conn) {
        setSel(at);
        startStream(at);
        break;
      }
    }
  }, [ags?.find(a => a.status === "running")?.status]);

  // Auto-scroll streaming log: scroll to bottom when new events arrive
  useEffect(() => {
    for (const at of A) {
      const state = ss[at];
      if (!state || !state.evts.length) continue;
      if (autoRef.current[at] !== false) {
        const el = logRef.current[at];
        if (el) el.scrollTop = el.scrollHeight;
      }
    }
  });

  const startStream = (at: AgentType) => {
    // Always reconnect — keep existing events and append new ones
    esRef.current?.close();
    setSs((p) => ({ ...p, [at]: { evts: [], conn: false, done: false, showH: false } }));
    autoRef.current[at] = true;
    const es = new EventSource(`/api/projects/${id}/agents/${at}/stream`);
    esRef.current = es;
    es.onopen = () => setSs((p) => ({ ...p, [at]: { ...(p[at] || { evts: [], done: false, showH: false }), conn: true } }));
    es.onerror = () => { es.close(); setSs((p) => ({ ...p, [at]: { ...(p[at] || { evts: [], done: false, showH: false }), conn: false, done: true } })); };
    es.onmessage = (e) => {
      try {
        const evt: E = JSON.parse(e.data);
        if (evt.type === "output" && evt.content) {
          const data = evt.content as Record<string, unknown>;
          setOut((p) => ({ ...p, [at]: data }));
          // Add to history (accumulate across multiple runs)
          const tsKey = `${at}_${Date.now()}`;
          setOutHistory((p) => {
            // Deduplicate: if same output already exists, skip
            const exists = p.some(h => h.agent === at && JSON.stringify(h.data) === JSON.stringify(data));
            if (exists) return p;
            return [...p, { key: tsKey, agent: at, data, ts: Date.now() }];
          });
        }
        setSs((p) => {
          const c = p[at] || { evts: [], conn: false, done: false, showH: false };
          const n = { ...c, evts: [...c.evts, evt] };
          if (evt.type === "done" || evt.type === "output") { n.done = true; n.conn = false; es.close(); }
          return { ...p, [at]: n };
        });
      } catch {}
    };
  };

  const hClick = async (at: AgentType) => {
    if (at === sel) { setSel(null); return; }
    setSel(at);
    const a = abm.get(at);
    if (a?.status === "completed" && !out[at]) {
      try { const o = await getAgentOutput(id!, at).catch(() => null); setOut((p) => ({ ...p, [at]: o as Record<string, unknown> | null })); } catch {}
    }
    if (a?.status === "running") startStream(at);
  };

  // Re-run a specific agent (for completed or failed)
  const reRunAgent = (at: AgentType) => {
    // Clear old output so it shows "loading..." until new results arrive
    setOut((p) => { const n = { ...p }; delete n[at]; return n; });
    autoRef.current[at] = true;
    setSel(at);
    const es = new EventSource(`/api/projects/${id}/agents/${at}/stream`);
    esRef.current = es;
    es.onerror = () => {};
    let firstEvent = true;
    es.onmessage = (e) => {
      try {
        const evt: E = JSON.parse(e.data);
        if (firstEvent && evt.type !== "output") {
          // Replace old events on first real event
          firstEvent = false;
          setSs((p) => ({ ...p, [at]: { evts: [], conn: true, done: false, showH: true } }));
        }
        if (evt.type === "output" && evt.content) {
          const data = evt.content as Record<string, unknown>;
          setOut((p) => ({ ...p, [at]: data }));
          const tsKey = `${at}_${Date.now()}`;
          setOutHistory((p) => {
            const exists = p.some(h => h.agent === at && JSON.stringify(h.data) === JSON.stringify(data));
            if (exists) return p;
            return [...p, { key: tsKey, agent: at, data, ts: Date.now() }];
          });
        }
        setSs((p) => {
          const c = p[at] || { evts: [], conn: false, done: false, showH: true };
          const n = { ...c, evts: [...c.evts, evt] };
          if (evt.type === "done" || evt.type === "output") { n.done = true; n.conn = false; es.close(); }
          if (evt.type === "error") { n.done = true; n.conn = false; es.close(); }
          return { ...p, [at]: n };
        });
      } catch {}
    };
  };

  useEffect(() => {
    if (!sel) return;
    const a = abm.get(sel);
    if (a?.status === "running" && !ss[sel]?.evts.length) startStream(sel);
    if (a?.status === "completed" && !out[sel]) {
      getAgentOutput(id!, sel).then(o => { if (o) setOut((p) => ({ ...p, [sel]: o as Record<string, unknown> | null })); }).catch(() => {});
    }
  }, [ags, sel]);

  // Auto-select running agent so user sees streaming
  useEffect(() => {
    for (const at of A) {
      const a = abm.get(at);
      if (a?.status === "running" && sel !== at) {
        setSel(at);
        startStream(at);
        break;
      }
    }
  }, [ags]);
  useEffect(() => () => { esRef.current?.close(); }, []);

  if (!pj) return <Container><p style={{ padding: spacing.xxl, color: colors.error }}>项目未找到</p></Container>;
  const pys = P(pj.status as ProjectStatus);
  const canS = pj.status === "new" || pj.status === "failed";

  // File collector: aggregate from DB result_json + streaming output + history
  interface FileEntry { name: string; ag: string; fn: string; url?: string; ts: number; }
  const fls: FileEntry[] = [];
  let fi = 1;
  const seenFns = new Set<string>();
  // Collect from history (accumulated across runs — never disappears)
  for (const h of outHistory) {
    const rj = h.data;
    const ts = h.ts || Date.now();
    if (rj?.ppt_url) { const f: FileEntry = { name: `#${fi++} 方案PPT [${I[h.agent].t}]`, ag: I[h.agent].t, fn: `${h.key}_方案.pptx`, url: rj.ppt_url as string, ts }; if (!seenFns.has(f.name)) { fls.push(f); seenFns.add(f.name); } }
    if (rj?.excel_url) { const f: FileEntry = { name: `#${fi++} 报价Excel [${I[h.agent].t}]`, ag: I[h.agent].t, fn: `${h.key}_报价.xlsx`, url: rj.excel_url as string, ts }; if (!seenFns.has(f.name)) { fls.push(f); seenFns.add(f.name); } }
    if (rj?.error_report_url) { const f: FileEntry = { name: `#${fi++} 错误报告 [${I[h.agent].t}]`, ag: I[h.agent].t, fn: `${h.key}_错误报告.xlsx`, url: rj.error_report_url as string, ts }; if (!seenFns.has(f.name)) { fls.push(f); seenFns.add(f.name); } }
    const jsonF: FileEntry = { name: `#${fi++} ${I[h.agent].t}输出`, ag: I[h.agent].t, fn: `${h.key}_output.json`, ts };
    if (!seenFns.has(jsonF.name)) { fls.push(jsonF); seenFns.add(jsonF.name); }
  }
  // Also collect current streaming output if not already in history
  for (const at of A) {
    const a = abm.get(at);
    const rj = (a?.result_json || out[at]) as Record<string, unknown> | null;
    if (!rj) continue;
    const isInHistory = outHistory.some(h => h.agent === at && JSON.stringify(h.data) === JSON.stringify(rj));
    if (isInHistory) continue;
    if (a?.status === "completed" || out[at]) {
      // Stable timestamp: use stored ref, only set once
      const fnBase = `${at}_`;
      if (rj?.ppt_url) { const key = fnBase + "ppt"; if (!fileTsRef.current[key]) fileTsRef.current[key] = Date.now(); fls.push({ name: `#${fi++} 方案PPT`, ag: I[at].t, fn: `${at}_方案.pptx`, url: rj.ppt_url as string, ts: fileTsRef.current[key] }); }
      if (rj?.excel_url) { const key = fnBase + "xls"; if (!fileTsRef.current[key]) fileTsRef.current[key] = Date.now(); fls.push({ name: `#${fi++} 报价Excel`, ag: I[at].t, fn: `${at}_报价.xlsx`, url: rj.excel_url as string, ts: fileTsRef.current[key] }); }
      if (rj?.error_report_url) { const key = fnBase + "err"; if (!fileTsRef.current[key]) fileTsRef.current[key] = Date.now(); fls.push({ name: `#${fi++} 错误报告`, ag: I[at].t, fn: `${at}_错误报告.xlsx`, url: rj.error_report_url as string, ts: fileTsRef.current[key] }); }
      const jsonKey = fnBase + "json"; if (!fileTsRef.current[jsonKey]) fileTsRef.current[jsonKey] = Date.now(); fls.push({ name: `#${fi++} ${I[at].t}数据`, ag: I[at].t, fn: `${at}_output.json`, ts: fileTsRef.current[jsonKey] });
    }
  }
  // Sort by timestamp: oldest first → newest last
  fls.sort((a, b) => a.ts - b.ts);

  const onLogScroll = (at: AgentType) => (e: React.UIEvent<HTMLDivElement>) => {
    const t = e.currentTarget;
    autoRef.current[at] = (t.scrollHeight - t.scrollTop - t.clientHeight) < 20;
  };

  return (
    <Container>
      <div style={{ padding: `${spacing.xxl}px 0` }}>
        <Button variant="text-link" onClick={() => nav("/dashboard")} style={{ marginBottom: spacing.lg }}>&larr; 返回项目列表</Button>
        <div style={{ display: "flex", alignItems: "center", gap: spacing.md, marginBottom: spacing.sm, flexWrap: "wrap" }}>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 600, lineHeight: 1.15, letterSpacing: "-1px", color: colors.ink }}>{pj.name}</h1>
          <Badge background={pys.bg} color={pys.text}>{STATUS_LABELS[pj.status as ProjectStatus]}</Badge>
        </div>
        {pj.description && <p style={{ fontFamily: "var(--font-body)", fontSize: 16, color: colors.body, marginBottom: spacing.lg }}>{pj.description}</p>}
        {pj.api_config_id && acs && (
          <div style={{ marginBottom: spacing.lg }}><span style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted }}>API: </span><span style={{ fontFamily: "var(--font-code)", fontSize: 14, color: colors.ink }}>{acs.find(c => c.id === pj.api_config_id)?.display_name || `#${pj.api_config_id}`}</span></div>
        )}
        {canS && (
          <div style={{ backgroundColor: colors.surfaceCard, borderRadius: rounded.lg, padding: spacing.xl, marginBottom: spacing.xl }}>
            <h2 style={{ fontFamily: "var(--font-body)", fontSize: 18, fontWeight: 600, color: colors.ink, marginBottom: spacing.md }}>准备启动项目</h2>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted, marginBottom: spacing.lg }}>上传客户需求文档（Word/PDF/TXT），然后点击"开始分析"启动 AI Agent 工作流。</p>
            <div style={{ marginBottom: spacing.lg }}>
              <input ref={fiRef} type="file" multiple accept=".pdf,.docx,.txt,.xlsx" onChange={async (e) => { const files = Array.from(e.target.files || []); for (const file of files) { try { const fd = new FormData(); fd.append("file", file); await fetch(`/api/projects/${id}/documents`, { method: "POST", body: fd }); } catch {} }; qc.invalidateQueries({ queryKey: ["docs", id] }); }} style={{ display: "none" }} />
              <Button variant="secondary" onClick={() => fiRef.current?.click()}>选择文件</Button>
              {uploadedDocNames.length > 0 && (
                <div style={{ marginTop: spacing.sm }}>
                  {uploadedDocNames.map((f, i) => <div key={i} style={{ fontFamily: "var(--font-code)", fontSize: 13, color: colors.ink, padding: "4px 0" }}>{f}</div>)}
                </div>
              )}
            </div>
            <Button variant="primary" disabled={starting} onClick={() => { setStarting(true); tm.mutate(); }}>{starting ? "启动中..." : "开始分析"}</Button>
            {starting && <p style={{ fontFamily: "var(--font-body)", fontSize: 13, color: colors.muted, marginTop: spacing.sm }}>正在调度 Agent 工作流，请稍候...</p>}
          </div>
        )}
        {!canS && uploadedDocNames.length > 0 && (
          <div style={{ backgroundColor: colors.surfaceCard, borderRadius: rounded.lg, padding: spacing.lg, marginBottom: spacing.lg }}>
            <h3 style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 600, color: colors.ink, marginBottom: spacing.sm }}>已上传文档</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: spacing.xs }}>
              {uploadedDocNames.map((f, i) => (
                <span key={i} style={{ fontFamily: "var(--font-code)", fontSize: 13, color: colors.ink, backgroundColor: colors.canvas, padding: "6px 12px", borderRadius: rounded.md, border: `1px solid ${colors.hairline}` }}>{f}</span>
              ))}
            </div>
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: isNarrow ? "1fr" : "minmax(0, 1fr) minmax(0, 1fr)", gap: spacing.lg, alignItems: "start" }}>
          {/* LEFT: Workflow */}
          <div style={{ backgroundColor: colors.surfaceCard, borderRadius: rounded.lg, padding: spacing.xl }}>
            <h2 style={{ fontFamily: "var(--font-body)", fontSize: 18, fontWeight: 600, color: colors.ink, marginBottom: spacing.lg }}>工作流进度</h2>
            {A.map((at, idx) => {
              const a = abm.get(at);
              const status = (a?.status as AgentStatus) ?? "pending";
              const s = S(status);
              const isS = sel === at;
              const isL = idx === A.length - 1;
              const info = I[at];
              const st = ss[at] || { evts: [], conn: false, done: false, showH: false };
              const tokens = st.evts.filter(e => e.type === "token").map(e => String(e.content || "")).join("");
              const nonT = st.evts.filter(e => e.type !== "token");
              const hasStream = st.evts.length > 0;
              const op = out[at];

              return (
                <div key={at} style={{ display: "flex", gap: spacing.md }}>
                  {/* Timeline column — stretches with content */}
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 24, flexShrink: 0 }}>
                    <div onClick={() => hClick(at)} style={{ width: 24, height: 24, borderRadius: "50%", backgroundColor: s.bg, display: "flex", alignItems: "center", justifyContent: "center", color: s.t, fontSize: 12, fontWeight: 600, cursor: "pointer", flexShrink: 0, transition: "transform 0.15s", transform: isS ? "scale(1.2)" : "scale(1)" }}>
                      {status === "running" ? "⋯" : idx + 1}
                    </div>
                    {!isL && <div style={{ width: 2, flex: 1, backgroundColor: status === "completed" ? colors.success : colors.hairline, marginTop: 0 }} />}
                  </div>

                  {/* Content column — determines row height, line stretches to match */}
                  <div style={{ flex: 1, paddingBottom: isL ? 0 : spacing.lg, minWidth: 0 }}>
                    <div onClick={() => hClick(at)} style={{ cursor: "pointer" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: 4, justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
                          <span style={{ fontFamily: "var(--font-body)", fontSize: 16, fontWeight: 600, color: colors.ink }}>{info.t}</span>
                          <Badge background={s.bg} color={s.t}>{s.l}</Badge>
                          <span style={{ fontFamily: "var(--font-body)", fontSize: 11, color: colors.mutedSoft }}>
                            {isS ? "▲ 收起" : "▼ 展开"}
                          </span>
                        </div>
                        {(status === "completed" || status === "failed") && (
                          <span
                            onClick={(e) => { e.stopPropagation(); reRunAgent(at); }}
                            title="重新执行此 Agent"
                            style={{
                              fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 500,
                              color: colors.muted, cursor: "pointer",
                              padding: "2px 8px", borderRadius: rounded.sm,
                              border: `1px solid ${colors.hairline}`,
                              transition: "all 0.15s",
                              backgroundColor: "transparent",
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.color = colors.ink; e.currentTarget.style.borderColor = colors.ink; e.currentTarget.style.backgroundColor = colors.surfaceCard; }}
                            onMouseLeave={(e) => { e.currentTarget.style.color = colors.muted; e.currentTarget.style.borderColor = colors.hairline; e.currentTarget.style.backgroundColor = "transparent"; }}
                          >
                            ↻ 重新执行
                          </span>
                        )}
                      </div>
                      <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted, margin: 0 }}>{info.d}</p>
                      {a?.error_message && <p style={{ fontFamily: "var(--font-code)", fontSize: 13, color: colors.error, marginTop: spacing.xs, marginBottom: 0 }}>{a.error_message}</p>}
                    </div>

                    {/* Expanded section — inside the same row, so line stretches */}
                    {isS && (
                      <div style={{ marginTop: spacing.sm, padding: spacing.md, backgroundColor: colors.canvas, borderRadius: rounded.md, border: `1px solid ${colors.hairline}` }}>

                        {status === "running" && (
                          <div>
                            <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.sm }}>
                              <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: st.done && !st.conn ? colors.success : colors.success, transition: "background-color 0.3s" }} />
                              <span style={{ fontFamily: "var(--font-body)", fontSize: 13, color: colors.muted }}>
                                {st.done ? "正在生成文件..." : st.conn ? "实时监控中" : "连接..."}
                              </span>
                            </div>
                            <div ref={(el) => { logRef.current[at] = el; }} onScroll={onLogScroll(at)}
                              style={{ backgroundColor: colors.surfaceDark, borderRadius: rounded.md, padding: spacing.sm, paddingBottom: spacing.md, maxHeight: 260, overflow: "auto", fontFamily: "var(--font-code)", fontSize: 12, lineHeight: "20px", color: colors.onDarkSoft, scrollBehavior: "smooth" }}>
                              {!hasStream && <span style={{ color: colors.mutedSoft }}>等待 Agent 响应...</span>}
                              {nonT.map((evt, i) => (
                                <div key={i} style={{ padding: "2px 0", borderBottom: `1px solid ${colors.surfaceDarkElevated}` }}>
                                  {evt.type === "start" && <span style={{ color: colors.success }}>▶ {String(evt.model || "")} 工具: {(evt.tools || []).join(", ") || "无"}</span>}
                                  {evt.type === "log" && <span style={{ color: colors.success }}>{String(evt.content || "")}</span>}
                                  {evt.type === "tool_call" && <div><span style={{ color: colors.brandAccent }}>{evt.name}</span><span style={{ color: colors.mutedSoft }}> ({JSON.stringify(evt.args || {}).slice(0, 100)})</span></div>}
                                  {evt.type === "tool_result" && <div style={{ paddingLeft: spacing.md, color: colors.onDarkSoft }}>↳ {JSON.stringify(evt.result).slice(0, 200)}</div>}
                                  {evt.type === "error" && <span style={{ color: colors.error }}>✖ {String(evt.content || "")}</span>}
                                </div>
                              ))}
                              {tokens && <div style={{ color: colors.onDark, whiteSpace: "pre-wrap", padding: "4px 0", borderTop: `1px solid ${colors.surfaceDarkElevated}` }}>{tokens}</div>}
                            </div>
                          </div>
                        )}

                        {status === "completed" && (
                          <div>
                            {hasStream && (
                              <div style={{ marginBottom: spacing.sm }}>
                                <div onClick={() => setSs((p) => ({ ...p, [at]: { ...st, showH: !st.showH } }))}
                                  style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.brandAccent, cursor: "pointer", userSelect: "none", padding: "4px 0" }}>
                                  {st.showH ? "▲ 收起执行过程" : `▼ 查看执行过程 (${st.evts.filter(e => e.type === "tool_call").length}次工具调用)`}
                                </div>
                                {st.showH && (
                                  <div style={{ backgroundColor: colors.surfaceDark, borderRadius: rounded.md, padding: spacing.sm, paddingBottom: spacing.md, maxHeight: 300, overflow: "auto", fontFamily: "var(--font-code)", fontSize: 12, lineHeight: "20px", color: colors.onDarkSoft }}>
                                    {nonT.map((evt, i) => (
                                      <div key={i} style={{ padding: "2px 0", borderBottom: `1px solid ${colors.surfaceDarkElevated}` }}>
                                        {evt.type === "start" && <span style={{ color: colors.success }}>▶ {String(evt.model || "")} 工具: {(evt.tools || []).join(", ") || "无"}</span>}
                                  {evt.type === "log" && <span style={{ color: colors.success }}>{String(evt.content || "")}</span>}
                                        {evt.type === "think" && <span style={{ color: colors.mutedSoft }}>{String(evt.content || "")}</span>}
                                        {evt.type === "tool_call" && <div><span style={{ color: colors.brandAccent }}>{evt.name}</span><span style={{ color: colors.mutedSoft }}> ({JSON.stringify(evt.args || {}).slice(0, 100)})</span></div>}
                                        {evt.type === "tool_result" && <div style={{ paddingLeft: spacing.md, color: colors.onDarkSoft }}>↳ {JSON.stringify(evt.result).slice(0, 300)}</div>}
                                        {evt.type === "error" && <span style={{ color: colors.error }}>✖ {String(evt.content || "")}</span>}
                                        {evt.type === "output" && <pre style={{ color: colors.success, margin: 0, whiteSpace: "pre-wrap", backgroundColor: colors.surfaceDarkElevated, padding: spacing.xs, borderRadius: rounded.sm, marginTop: 0 }}>{JSON.stringify(evt.content, null, 2)}</pre>}
                                      </div>
                                    ))}
                                    {tokens && <div style={{ color: colors.onDark, whiteSpace: "pre-wrap", padding: "4px 0", borderTop: `1px solid ${colors.surfaceDarkElevated}` }}>{tokens}</div>}
                                  </div>
                                )}
                              </div>
                            )}
                            {op ? (
                              <div>
                                <h4 style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 600, color: colors.ink, marginBottom: spacing.xs }}>输出数据</h4>
                                <pre style={{ fontFamily: "var(--font-code)", fontSize: 12, color: colors.ink, whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0, maxHeight: 300, overflow: "auto", backgroundColor: colors.surfaceCard, padding: spacing.sm, borderRadius: rounded.sm }}>{JSON.stringify(op, null, 2)}</pre>
                              </div>
                            ) : <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted }}>加载输出数据...</p>}
                          </div>
                        )}
                        {status === "failed" && <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.error }}>执行失败: {a?.error_message || "未知错误"}</p>}
                        {status === "pending" && <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted }}>等待执行...</p>}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          {/* RIGHT: File Output */}
          <div style={{ backgroundColor: colors.surfaceCard, borderRadius: rounded.lg, padding: spacing.xl }}>
            <h2 style={{ fontFamily: "var(--font-body)", fontSize: 18, fontWeight: 600, color: colors.ink, marginBottom: spacing.lg }}>文件输出</h2>
            {fls.length === 0 ? (
              <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted }}>暂无生成文件。Agent 执行完成后，方案PPT、报价Excel、错误报告等将显示在这里，JSON 数据也可在此下载。</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: spacing.sm }}>
                {fls.map((f, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: spacing.sm, backgroundColor: colors.canvas, borderRadius: rounded.md, border: `1px solid ${colors.hairline}`, gap: spacing.sm }}>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 600, color: colors.ink, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</div>
                      <div style={{ fontFamily: "var(--font-body)", fontSize: 11, color: colors.muted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.ag} · {f.fn}</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, flexShrink: 0 }}>
                      <span style={{ fontFamily: "var(--font-code)", fontSize: 11, color: colors.mutedSoft, whiteSpace: "nowrap" }}>
                        {new Date(f.ts).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      <Button variant="secondary" style={{ fontSize: 12, padding: "4px 12px", height: 28, flexShrink: 0, whiteSpace: "nowrap", borderRadius: 6 }} onClick={() => {
                        if (f.url) { window.open(f.url, "_blank"); return; }
                        const at2 = A.find(a2 => I[a2].t === f.ag);
                        if (at2 && abm.get(at2)?.result_json) {
                          const blob = new Blob([JSON.stringify(abm.get(at2)!.result_json, null, 2)], { type: "application/json" });
                          const url = URL.createObjectURL(blob); const a3 = document.createElement("a"); a3.href = url; a3.download = f.fn; a3.click();
                        }
                      }}>下载</Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Container>
  );
}
