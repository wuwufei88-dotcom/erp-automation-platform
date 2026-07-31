import React, { useRef, useCallback } from "react";
import { colors } from "../../tokens/colors";
import { rounded } from "../../tokens/rounded";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "text-link" | "icon-circular";
}

const base: React.CSSProperties = {
  fontFamily: "var(--font-body)",
  fontSize: 14,
  fontWeight: 600,
  lineHeight: 1,
  cursor: "pointer",
  border: "none",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  transition: "all 0.15s ease",
};

const styles: Record<string, React.CSSProperties> = {
  primary: {
    ...base,
    backgroundColor: colors.primary,
    color: colors.onPrimary,
    borderRadius: rounded.md,
    padding: "12px 20px",
    height: 40,
  },
  secondary: {
    ...base,
    backgroundColor: colors.canvas,
    color: colors.ink,
    borderRadius: rounded.md,
    padding: "12px 20px",
    height: 40,
    border: `1px solid ${colors.hairline}`,
  },
  "text-link": {
    ...base,
    backgroundColor: "transparent",
    color: colors.ink,
    padding: 0,
    height: "auto",
  },
  "icon-circular": {
    ...base,
    backgroundColor: colors.canvas,
    color: colors.ink,
    borderRadius: rounded.full,
    width: 36,
    height: 36,
    padding: 0,
    border: `1px solid ${colors.hairline}`,
  },
};

const hoverStyles: Record<string, React.CSSProperties> = {
  primary: { backgroundColor: "#222222", transform: "translateY(-1px)", boxShadow: "0 2px 8px rgba(0,0,0,0.15)" },
  secondary: { backgroundColor: colors.surfaceCard, borderColor: colors.ink },
  "text-link": { color: colors.muted, backgroundColor: "rgba(0,0,0,0.04)" },
  "icon-circular": { backgroundColor: colors.surfaceCard, borderColor: colors.ink },
};

const defaultStyles: Record<string, React.CSSProperties> = {
  primary: { backgroundColor: colors.primary, transform: "translateY(0)", boxShadow: "none" },
  secondary: { backgroundColor: colors.canvas, borderColor: colors.hairline },
  "text-link": { color: colors.ink, backgroundColor: "transparent" },
  "icon-circular": { backgroundColor: colors.canvas, borderColor: colors.hairline },
};

export default function Button({ variant = "primary", style, disabled, children, ...props }: ButtonProps) {
  const ref = useRef<HTMLButtonElement>(null);

  const onEnter = useCallback(() => {
    if (!ref.current || disabled) return;
    const hs = hoverStyles[variant];
    for (const [k, v] of Object.entries(hs)) {
      (ref.current.style as any)[k] = v;
    }
  }, [variant, disabled]);

  const onLeave = useCallback(() => {
    if (!ref.current) return;
    const ds = defaultStyles[variant];
    for (const [k, v] of Object.entries(ds)) {
      (ref.current.style as any)[k] = v;
    }
  }, [variant]);

  const disabledStyle = disabled
    ? { backgroundColor: variant === "primary" ? colors.hairline : colors.canvas, color: colors.mutedSoft, cursor: "not-allowed", borderColor: "transparent" }
    : {};

  return (
    <button
      ref={ref}
      disabled={disabled}
      style={{ ...styles[variant], ...disabledStyle, ...style }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      {...props}
    >
      {children}
    </button>
  );
}
