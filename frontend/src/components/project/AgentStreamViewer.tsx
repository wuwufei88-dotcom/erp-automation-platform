import { useState, useEffect, useRef } from "react";
import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import { rounded } from "../../tokens/rounded";

interface StreamEvent {
  type: string;
  content?: unknown;
  name?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  model?: string;
  tools?: string[];
  iteration?: number;
}

interface Props {
  projectId: string;
  agentType: string;
  active: boolean;
}

export default function AgentStreamViewer({ projectId, agentType, active }: Props) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!active) {
      eventSourceRef.current?.close();
      setConnected(false);
      return;
    }

    setEvents([]);
    const url = `/api/projects/${projectId}/agents/${agentType}/stream`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => { setConnected(false); es.close(); };

    es.onmessage = (e) => {
      try {
        const event: StreamEvent = JSON.parse(e.data);
        if (event.type === "done") {
          es.close();
          setConnected(false);
          return;
        }
        setEvents((prev) => [...prev, event]);
      } catch {}
    };

    return () => { es.close(); setConnected(false); };
  }, [projectId, agentType, active]);

  if (!active) return null;

  return (
    <div style={{ padding: spacing.md }}>
      <div style={{ display: "flex", alignItems: "center", gap: spacing.sm, marginBottom: spacing.md }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          backgroundColor: connected ? colors.success : colors.hairline,
          transition: "background-color 0.2s",
        }} />
        <span style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.muted }}>
          {connected ? "实时连接中" : events.length > 0 ? "已完成" : "连接中..."}
        </span>
      </div>

      <div style={{
        backgroundColor: colors.surfaceDark,
        borderRadius: rounded.md,
        padding: spacing.sm,
        maxHeight: 400,
        overflow: "auto",
        fontFamily: "var(--font-code)",
        fontSize: 12,
        lineHeight: 1.6,
        color: colors.onDarkSoft,
      }}>
        {events.map((evt, i) => (
          <div key={i} style={{ padding: "2px 0", borderBottom: `1px solid ${colors.surfaceDarkElevated}` }}>
            {evt.type === "start" && (
              <span style={{ color: colors.success }}>
                ▶ Agent 启动 ({evt.model}) | 工具: {(evt.tools || []).join(", ") || "无"}
              </span>
            )}
            {evt.type === "think" && (
              <span style={{ color: colors.mutedSoft }}>💭 {String(evt.content || "")}</span>
            )}
            {evt.type === "tool_call" && (
              <div>
                <span style={{ color: colors.brandAccent }}>🔧 {evt.name}</span>
                <span style={{ color: colors.mutedSoft }}>
                  ({JSON.stringify(evt.args || {}, null, 0).slice(0, 120)})
                </span>
              </div>
            )}
            {evt.type === "tool_result" && (
              <div style={{ paddingLeft: spacing.md, color: colors.onDarkSoft }}>
                ↳ {JSON.stringify(evt.result, null, 0).slice(0, 200)}
              </div>
            )}
            {evt.type === "output" && (
              <pre style={{
                color: colors.success, margin: 0, whiteSpace: "pre-wrap",
                backgroundColor: colors.surfaceDarkElevated, padding: spacing.xs,
                borderRadius: rounded.sm, marginTop: 4,
              }}>
                {JSON.stringify(evt.content, null, 2)}
              </pre>
            )}
            {evt.type === "error" && (
              <span style={{ color: colors.error }}>✖ {String(evt.content || "")}</span>
            )}
            {evt.type === "warning" && (
              <span style={{ color: colors.warning }}>⚠ {String(evt.content || "")}</span>
            )}
          </div>
        ))}
        {events.length === 0 && (
          <span style={{ color: colors.mutedSoft }}>等待 Agent 响应...</span>
        )}
      </div>
    </div>
  );
}
