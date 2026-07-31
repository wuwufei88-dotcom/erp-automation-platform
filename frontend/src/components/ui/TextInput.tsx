import React from "react";
import { colors } from "../../tokens/colors";
import { rounded } from "../../tokens/rounded";

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export default function TextInput({ label, style, ...props }: TextInputProps) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {label && (
        <label style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, color: colors.ink }}>
          {label}
        </label>
      )}
      <input
        style={{
          fontFamily: "var(--font-body)",
          fontSize: 16,
          lineHeight: 1.5,
          color: colors.ink,
          backgroundColor: colors.canvas,
          borderRadius: rounded.md,
          padding: "10px 14px",
          height: 40,
          border: `1px solid ${colors.hairline}`,
          outline: "none",
          boxSizing: "border-box",
          ...style,
        }}
        {...props}
      />
    </div>
  );
}
