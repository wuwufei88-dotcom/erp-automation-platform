import { colors } from "../../tokens/colors";
import { rounded } from "../../tokens/rounded";

interface NavPillGroupProps {
  items: string[];
  activeIndex: number;
  onChange: (index: number) => void;
}

export default function NavPillGroup({ items, activeIndex, onChange }: NavPillGroupProps) {
  return (
    <div
      style={{
        display: "inline-flex",
        backgroundColor: colors.surfaceSoft,
        borderRadius: rounded.pill,
        padding: 4,
        gap: 2,
      }}
    >
      {items.map((item, i) => (
        <button
          key={item}
          onClick={() => onChange(i)}
          style={{
            fontFamily: "var(--font-body)",
            fontSize: 14,
            fontWeight: 500,
            lineHeight: 1.4,
            border: "none",
            cursor: "pointer",
            padding: "8px 14px",
            borderRadius: rounded.md,
            backgroundColor: i === activeIndex ? colors.canvas : "transparent",
            color: i === activeIndex ? colors.ink : colors.muted,
            boxShadow: i === activeIndex ? "0 1px 2px rgba(0,0,0,0.08)" : "none",
            transition: "all 0.15s",
          }}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
