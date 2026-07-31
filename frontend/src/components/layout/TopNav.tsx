import { Link, useNavigate, useLocation } from "react-router-dom";
import { colors } from "../../tokens/colors";
import Button from "../ui/Button";
import Container from "./Container";

const navItems = [
  { label: "首页", path: "/" },
  { label: "方案", path: "/solutions" },
  { label: "资源", path: "/resources" },
  { label: "API 管理", path: "/settings/api" },
];

export default function TopNav() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === "/" && location.pathname === "/") return true;
    if (path === "/dashboard" && (location.pathname.startsWith("/dashboard") || location.pathname.startsWith("/projects"))) return true;
    return location.pathname === path || location.pathname.startsWith(path + "/");
  };

  return (
    <nav
      style={{
        height: 64,
        backgroundColor: colors.canvas,
        borderBottom: `1px solid ${colors.hairlineSoft}`,
        display: "flex",
        alignItems: "center",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <Container>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
          <Link
            to="/"
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 22,
              fontWeight: 600,
              color: colors.ink,
              textDecoration: "none",
              letterSpacing: "-0.5px",
            }}
          >
            ERP Hub
          </Link>

          <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
            {navItems.map((item) => {
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 14,
                    fontWeight: active ? 600 : 400,
                    color: active ? colors.ink : colors.muted,
                    textDecoration: "none",
                    transition: "all 0.15s",
                    padding: "4px 0",
                    borderBottom: active ? `2px solid ${colors.ink}` : "2px solid transparent",
                  }}
                  onMouseEnter={(e) => { if (!active) { e.currentTarget.style.color = colors.ink; } }}
                  onMouseLeave={(e) => { if (!active) { e.currentTarget.style.color = colors.muted; } }}
                >
                  {item.label}
                </Link>
              );
            })}
            <Button variant="primary" onClick={() => navigate("/dashboard")}>
              交付项目
            </Button>
          </div>
        </div>
      </Container>
    </nav>
  );
}
