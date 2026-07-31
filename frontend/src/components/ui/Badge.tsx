import React from "react";
import { colors } from "../../tokens/colors";
import { rounded } from "../../tokens/rounded";

interface BadgeProps {
  children: React.ReactNode;
  color?: string;
  background?: string;
}

export default function Badge({ children, color = colors.ink, background = colors.surfaceCard }: BadgeProps) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontFamily: "var(--font-body)",
        fontSize: 13,
        fontWeight: 500,
        lineHeight: 1.4,
        color,
        backgroundColor: background,
        borderRadius: rounded.pill,
        padding: "4px 12px",
      }}
    >
      {children}
    </span>
  );
}
