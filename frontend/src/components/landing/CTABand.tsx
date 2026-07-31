import { useNavigate } from "react-router-dom";
import Button from "../ui/Button";
import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import { rounded } from "../../tokens/rounded";
import Container from "../layout/Container";

export default function CTABand() {
  const navigate = useNavigate();

  return (
    <section style={{ padding: `${spacing.section}px 0`, backgroundColor: colors.canvas }}>
      <Container>
        <div
          style={{
            backgroundColor: colors.surfaceCard,
            borderRadius: rounded.lg,
            padding: spacing.xxl,
            textAlign: "center",
          }}
        >
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 28,
              fontWeight: 600,
              lineHeight: 1.2,
              letterSpacing: "-0.5px",
              color: colors.ink,
              marginBottom: spacing.md,
            }}
          >
            准备好开始自动化 ERP 交付了吗？
          </h2>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: 16,
              lineHeight: 1.5,
              color: colors.body,
              marginBottom: spacing.xl,
            }}
          >
            创建你的第一个项目，体验 AI 驱动的智能化交付流程。
          </p>
          <Button variant="primary" onClick={() => navigate("/dashboard")}>
            免费开始使用
          </Button>
        </div>
      </Container>
    </section>
  );
}
