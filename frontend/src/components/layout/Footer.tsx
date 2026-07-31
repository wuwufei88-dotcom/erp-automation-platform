import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import Container from "./Container";

const linkGroups = [
  {
    title: "产品",
    links: ["需求解析", "方案生成", "系统配置", "数据迁移", "运维答疑"],
  },
  {
    title: "方案",
    links: ["YonSuite", "NC Cloud", "U8+", "定制开发"],
  },
  {
    title: "公司",
    links: ["关于我们", "客户案例", "合作伙伴", "加入我们"],
  },
  {
    title: "资源",
    links: ["帮助中心", "API 文档", "系统状态", "联系我们"],
  },
];

export default function Footer() {
  return (
    <footer
      style={{
        backgroundColor: colors.surfaceDark,
        padding: "64px 0",
      }}
    >
      <Container>
        <div style={{ marginBottom: spacing.xxl }}>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 22,
              fontWeight: 600,
              color: colors.onDark,
              letterSpacing: "-0.5px",
            }}
          >
            ERP Hub
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: spacing.lg,
          }}
        >
          {linkGroups.map((group) => (
            <div key={group.title}>
              <h4
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: 14,
                  fontWeight: 600,
                  color: colors.onDark,
                  marginBottom: spacing.md,
                }}
              >
                {group.title}
              </h4>
              <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: spacing.xs }}>
                {group.links.map((link) => (
                  <li key={link}>
                    <button
                      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
                      style={{
                        fontFamily: "var(--font-body)",
                        fontSize: 14,
                        fontWeight: 400,
                        lineHeight: 1.5,
                        color: colors.onDarkSoft,
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 0,
                      }}
                    >
                      {link}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: spacing.xxl,
            paddingTop: spacing.lg,
            borderTop: `1px solid ${colors.surfaceDarkElevated}`,
          }}
        >
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 13,
              fontWeight: 400,
              color: colors.onDarkSoft,
            }}
          >
            &copy; {new Date().getFullYear()} ERP Hub. All rights reserved.
          </p>
        </div>
      </Container>
    </footer>
  );
}
