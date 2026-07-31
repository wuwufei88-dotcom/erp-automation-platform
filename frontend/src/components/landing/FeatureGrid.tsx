import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import { rounded } from "../../tokens/rounded";
import Container from "../layout/Container";

const features = [
  {
    icon: "1",
    title: "需求解析",
    description: "自动解析客户需求文档，提取组织架构、模块清单、定制需求，生成结构化需求规格。",
  },
  {
    icon: "2",
    title: "方案生成",
    description: "基于历史项目案例和行业模板，自动生成实施方案、报价单和培训课件。",
  },
  {
    icon: "3",
    title: "系统配置",
    description: "调用 ERP 开放 API 自动初始化组织、审批流、基础档案，标准化配置一键完成。",
  },
  {
    icon: "4",
    title: "数据迁移",
    description: "智能映射源系统字段，自动清洗去重，分批安全导入历史数据到目标 ERP 系统。",
  },
  {
    icon: "5",
    title: "运维问答",
    description: "7×24 智能运维助手，实时诊断故障、检索知识库、推送告警通知。",
  },
];

export default function FeatureGrid() {
  return (
    <section style={{ padding: `${spacing.section}px 0`, backgroundColor: colors.surfaceSoft }}>
      <Container>
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 48,
            fontWeight: 600,
            lineHeight: 1.1,
            letterSpacing: "-1.5px",
            color: colors.ink,
            textAlign: "center",
            marginBottom: spacing.md,
          }}
        >
          五大 AI Agent，全流程自动化
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: 16,
            lineHeight: 1.5,
            color: colors.muted,
            textAlign: "center",
            maxWidth: 600,
            margin: "0 auto",
            marginBottom: spacing.xxl,
          }}
        >
          每个 Agent 专注于单一业务领域，通过调度中心协同编排，实现通用 ERP 项目端到端自动化交付
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: spacing.lg,
          }}
        >
          {features.map((f) => (
            <div
              key={f.title}
              style={{
                backgroundColor: colors.surfaceCard,
                borderRadius: rounded.lg,
                padding: spacing.xl,
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: rounded.md,
                  backgroundColor: colors.canvas,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: "var(--font-body)",
                  fontSize: 18,
                  fontWeight: 600,
                  color: colors.ink,
                  marginBottom: spacing.lg,
                }}
              >
                {f.icon}
              </div>
              <h3
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 18,
                  fontWeight: 600,
                  lineHeight: 1.4,
                  color: colors.ink,
                  marginBottom: spacing.sm,
                }}
              >
                {f.title}
              </h3>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 16,
                  fontWeight: 400,
                  lineHeight: 1.5,
                  color: colors.body,
                }}
              >
                {f.description}
              </p>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
