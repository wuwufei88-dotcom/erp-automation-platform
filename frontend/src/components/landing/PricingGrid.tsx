import { useNavigate } from "react-router-dom";
import Button from "../ui/Button";
import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import { rounded } from "../../tokens/rounded";
import Container from "../layout/Container";

const tiers = [
  {
    name: "入门版",
    price: "¥9,800",
    period: "/月",
    description: "适合小型实施团队",
    features: ["需求解析 Agent", "方案生成 Agent", "最多 5 个并发项目", "基础文档解析", "邮件技术支持"],
    featured: false,
  },
  {
    name: "专业版",
    price: "¥29,800",
    period: "/月",
    description: "适合中型实施公司",
    features: ["全部 5 个 Agent", "ERP 系统自动配置", "数据迁移与清洗", "最多 20 个并发项目", "企业微信集成", "7×24 运维答疑", "优先技术支持"],
    featured: true,
  },
  {
    name: "企业版",
    price: "定制",
    period: "",
    description: "适合大型实施伙伴",
    features: ["私有化部署", "无限并发项目", "定制 Agent 开发", "专属知识库训练", "SLA 保障", "驻场培训服务"],
    featured: false,
  },
];

export default function PricingGrid() {
  const navigate = useNavigate();

  return (
    <section style={{ padding: `${spacing.section}px 0`, backgroundColor: colors.canvas }}>
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
          透明的价格方案
        </h2>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: 16,
            lineHeight: 1.5,
            color: colors.muted,
            textAlign: "center",
            maxWidth: 500,
            margin: "0 auto",
            marginBottom: spacing.xxl,
          }}
        >
          从小团队到企业级，找到适合你的方案
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: spacing.lg,
            alignItems: "start",
          }}
        >
          {tiers.map((tier) => (
            <div
              key={tier.name}
              style={{
                backgroundColor: tier.featured ? colors.surfaceDark : colors.canvas,
                color: tier.featured ? colors.onDark : colors.ink,
                borderRadius: rounded.lg,
                padding: spacing.xl,
                border: tier.featured ? "none" : `1px solid ${colors.hairline}`,
              }}
            >
              <h3
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 22,
                  fontWeight: 600,
                  lineHeight: 1.3,
                  letterSpacing: "-0.3px",
                  marginBottom: spacing.xs,
                }}
              >
                {tier.name}
              </h3>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 14,
                  color: tier.featured ? colors.onDarkSoft : colors.muted,
                  marginBottom: spacing.lg,
                }}
              >
                {tier.description}
              </p>

              <div style={{ marginBottom: spacing.lg }}>
                <span
                  style={{
                    fontFamily: "var(--font-display)",
                    fontSize: 28,
                    fontWeight: 600,
                    lineHeight: 1.2,
                    letterSpacing: "-0.5px",
                  }}
                >
                  {tier.price}
                </span>
                <span
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 14,
                    color: tier.featured ? colors.onDarkSoft : colors.muted,
                  }}
                >
                  {tier.period}
                </span>
              </div>

              <ul style={{ listStyle: "none", marginBottom: spacing.xl }}>
                {tier.features.map((f) => (
                  <li
                    key={f}
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: 16,
                      lineHeight: 1.5,
                      padding: "6px 0",
                      display: "flex",
                      alignItems: "center",
                      gap: spacing.sm,
                    }}
                  >
                    <span style={{ color: tier.featured ? colors.success : colors.ink }}>&#10003;</span>
                    {f}
                  </li>
                ))}
              </ul>

              <Button
                variant={tier.featured ? "primary" : "secondary"}
                onClick={() => navigate("/dashboard")}
                style={
                  tier.featured
                    ? { backgroundColor: colors.onDark, color: colors.surfaceDark, width: "100%" }
                    : { width: "100%" }
                }
              >
                选择{tier.name}
              </Button>
            </div>
          ))}
        </div>
      </Container>
    </section>
  );
}
