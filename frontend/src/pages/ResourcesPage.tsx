import { colors } from "../tokens/colors";
import { spacing } from "../tokens/spacing";
import { rounded } from "../tokens/rounded";
import Container from "../components/layout/Container";

export default function ResourcesPage() {
  return (
    <Container>
      <div style={{ padding: `${spacing.xxl}px 0` }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 600, lineHeight: 1.15, letterSpacing: "-1px", color: colors.ink, marginBottom: spacing.md }}>
          资源中心
        </h1>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 16, color: colors.body, marginBottom: spacing.xl }}>
          ERP 实施工具、模板和最佳实践
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: spacing.lg }}>
          {[
            { title: "帮助中心", desc: "详细的使用指南和常见问题解答" },
            { title: "API 文档", desc: "完整的 REST API 接口说明和示例" },
            { title: "实施模板", desc: "项目章程、需求规格、测试用例等模板" },
            { title: "知识库", desc: "ERP 行业最佳实践和实施经验" },
            { title: "版本更新", desc: "平台最新功能和改进记录" },
            { title: "联系我们", desc: "技术支持和服务咨询" },
          ].map((r) => (
            <div key={r.title} style={{ backgroundColor: colors.surfaceCard, borderRadius: rounded.lg, padding: spacing.xl }}>
              <h3 style={{ fontFamily: "var(--font-body)", fontSize: 18, fontWeight: 600, color: colors.ink, marginBottom: spacing.xs }}>
                {r.title}
              </h3>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted }}>{r.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </Container>
  );
}
