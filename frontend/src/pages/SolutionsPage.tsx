import { colors } from "../tokens/colors";
import { spacing } from "../tokens/spacing";
import { rounded } from "../tokens/rounded";
import Container from "../components/layout/Container";

export default function SolutionsPage() {
  return (
    <Container>
      <div style={{ padding: `${spacing.xxl}px 0` }}>
        <h1 style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 600, lineHeight: 1.15, letterSpacing: "-1px", color: colors.ink, marginBottom: spacing.md }}>
          ERP 解决方案
        </h1>
        <p style={{ fontFamily: "var(--font-body)", fontSize: 16, color: colors.body, marginBottom: spacing.xl }}>
          通用 ERP 自动化交付 — 支持 JEECG、Odoo、ERPNext、SAP、Dynamics 365、用友 YonSuite 等主流 ERP 系统
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: spacing.lg }}>
          {[
            { name: "JEECG", desc: "开源低代码平台", modules: "组织管理、权限、工作流、报表" },
            { name: "Odoo", desc: "全球最流行的开源 ERP", modules: "销售、财务、HR、制造、库存" },
            { name: "ERPNext", desc: "开源 ERP 框架（Frappe）", modules: "财务、HR、制造、CRM" },
            { name: "金蝶云", desc: "中国主流企业级 ERP 云平台", modules: "财务、供应链、制造、HR" },
            { name: "SAP S/4HANA", desc: "全球最大的企业级 ERP", modules: "财务、供应链、制造、销售" },
            { name: "Dynamics 365 BC", desc: "Microsoft 企业 ERP", modules: "财务、供应链、项目管理" },
            { name: "用友 YonSuite", desc: "中国最大的云 ERP 平台", modules: "财务、供应链、制造、HR" },
          ].map((s) => (
            <div key={s.name} style={{ backgroundColor: colors.surfaceCard, borderRadius: rounded.lg, padding: spacing.xl }}>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, color: colors.ink, marginBottom: spacing.xs }}>
                {s.name}
              </h3>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 16, color: colors.body, marginBottom: spacing.sm }}>
                {s.desc}
              </p>
              <p style={{ fontFamily: "var(--font-body)", fontSize: 14, color: colors.muted }}>
                覆盖模块：{s.modules}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Container>
  );
}
