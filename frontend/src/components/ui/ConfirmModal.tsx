import Button from "./Button";
import { colors } from "../../tokens/colors";
import { spacing } from "../../tokens/spacing";
import { rounded } from "../../tokens/rounded";

interface ConfirmModalProps {
  show: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  variant?: "danger" | "default";
}

export default function ConfirmModal({
  show,
  title,
  message,
  confirmLabel = "确定",
  cancelLabel = "取消",
  onConfirm,
  onCancel,
  variant = "default",
}: ConfirmModalProps) {
  if (!show) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0,0,0,0.3)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 300,
      }}
      onClick={onCancel}
    >
      <div
        style={{
          backgroundColor: colors.canvas,
          borderRadius: rounded.lg,
          padding: spacing.xl,
          width: 420,
          maxWidth: "90vw",
          textAlign: "center",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontSize: 20,
            fontWeight: 600,
            color: colors.ink,
            marginBottom: spacing.sm,
          }}
        >
          {title}
        </div>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: 14,
            color: colors.muted,
            marginBottom: spacing.xl,
            lineHeight: 1.5,
          }}
        >
          {message}
        </p>
        <div style={{ display: "flex", gap: spacing.sm, justifyContent: "center" }}>
          <Button variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            variant="primary"
            onClick={onConfirm}
            style={
              variant === "danger"
                ? { backgroundColor: colors.error, borderColor: colors.error }
                : {}
            }
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
