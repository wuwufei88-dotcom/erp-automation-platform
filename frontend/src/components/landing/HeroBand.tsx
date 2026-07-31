import { useNavigate } from "react-router-dom";
import Button from "../ui/Button";
import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import { rounded } from "../../tokens/rounded";
import Container from "../layout/Container";

export default function HeroBand() {
  const navigate = useNavigate();

  return (
    <section style={{ padding: `${spacing.section}px 0`, backgroundColor: colors.canvas }}>
      <Container>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "7fr 5fr",
            gap: spacing.xxl,
            alignItems: "center",
          }}
        >
          <div>
            <h1
              style={{
                fontFamily: "var(--font-display)",
                fontSize: 64,
                fontWeight: 600,
                lineHeight: 1.05,
                letterSpacing: "-2px",
                color: colors.ink,
                marginBottom: spacing.lg,
              }}
            >
              通用 ERP 交付
              <br />
              智能化自动平台
            </h1>
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: 18,
                fontWeight: 400,
                lineHeight: 1.5,
                color: colors.body,
                marginBottom: spacing.xl,
                maxWidth: 480,
              }}
            >
              5 个 AI 子 Agent 协同工作，从需求解析到运维答疑，
              全流程自动化 ERP 项目实施交付。
            </p>
            <div style={{ display: "flex", gap: spacing.sm }}>
              <Button variant="primary" onClick={() => navigate("/dashboard")}>
                立即开始
              </Button>
              <Button variant="secondary" onClick={() => navigate("/dashboard")}>
                预约演示
              </Button>
            </div>
          </div>

          <div
            style={{
              backgroundColor: colors.canvas,
              borderRadius: rounded.xl,
              border: `1px solid ${colors.hairline}`,
              padding: spacing.lg,
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            }}
          >
            <div
              style={{
                backgroundColor: colors.surfaceCard,
                borderRadius: rounded.lg,
                padding: spacing.md,
                marginBottom: spacing.sm,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: spacing.sm }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: colors.success }} />
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.muted }}>
                  需求解析 Agent — 运行中
                </span>
              </div>
              <div style={{ fontFamily: "var(--font-code)", fontSize: 12, color: colors.muted }}>
                {">"} 解析客户组织架构... 完成{"\n"}
                {">"} 识别业务模块清单... 完成{"\n"}
                {">"} 提取定制化需求点... 进行中
              </div>
            </div>
            <div
              style={{
                backgroundColor: colors.surfaceCard,
                borderRadius: rounded.lg,
                padding: spacing.md,
                marginBottom: spacing.sm,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: spacing.sm }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: colors.hairline }} />
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.muted }}>
                  方案生成 Agent — 等待中
                </span>
              </div>
            </div>
            <div
              style={{
                backgroundColor: colors.surfaceCard,
                borderRadius: rounded.lg,
                padding: spacing.md,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: spacing.sm }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: colors.hairline }} />
                <span style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 500, color: colors.muted }}>
                  系统配置 Agent — 等待中
                </span>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
