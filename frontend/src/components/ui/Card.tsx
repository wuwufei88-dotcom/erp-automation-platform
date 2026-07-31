import React from "react";
import { colors } from "../../tokens/colors";
import { rounded } from "../../tokens/rounded";
import { spacing } from "../../tokens/spacing";

interface CardProps {
  children: React.ReactNode;
  variant?: "surface" | "canvas" | "dark" | "mockup";
  padding?: number;
  style?: React.CSSProperties;
}

const variants: Record<string, React.CSSProperties> = {
  surface: { backgroundColor: colors.surfaceCard, color: colors.ink },
  canvas: { backgroundColor: colors.canvas, color: colors.ink, border: `1px solid ${colors.hairline}` },
  dark: { backgroundColor: colors.surfaceDark, color: colors.onDark },
  mockup: { backgroundColor: colors.canvas, color: colors.ink, border: `1px solid ${colors.hairline}` },
};

export default function Card({ children, variant = "surface", padding = spacing.xl, style }: CardProps) {
  return (
    <div
      style={{
        borderRadius: rounded.lg,
        padding,
        ...variants[variant],
        ...style,
      }}
    >
      {children}
    </div>
  );
}
