"""
通用 ERP 自动化交付平台 — 一键启动器
双击运行即可启动全部服务
"""
import subprocess, sys, time, os, webbrowser, socket
from pathlib import Path

PYTHON = r"C:\Program Files\Python312\python.exe"
ROOT = Path(r"D:\project3")
JEECG = Path(r"D:\jeecg-boot")
FRONTEND_PORT = 5173
BACKEND_PORT = 8000


def kill_port(port: int):
    """Kill any process using the given port on Windows."""
    try:
        subprocess.run(
            f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill /F /PID %a >nul 2>&1',
            shell=True, capture_output=True,
        )
    except Exception:
        pass


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if something is listening on a port."""
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except Exception:
        return False


def run(cmd, cwd=None, capture=False):
    kwargs = {"shell": True}
    if cwd:
        kwargs["cwd"] = cwd
    if capture:
        kwargs["capture_output"] = True
    return subprocess.run(cmd, **kwargs)


def step(n, total, desc):
    print(f"\n  [{n}/{total}] {desc}")
    print(f"  {'─' * 45}")


def ok(msg):
    print(f"    ✓  {msg}")


def warn(msg):
    print(f"    ⚠  {msg}")


def main():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   通用 ERP 自动化交付平台 — 一键启动       ║")
    print("  ╚══════════════════════════════════════════════╝")

    total = 4

    # ── Step 1: Docker Infrastructure ──
    step(1, total, "Docker 基础设施 (MySQL/Redis/Milvus/MinIO)")
    r = run("docker compose up -d", cwd=str(ROOT), capture=True)
    if r.returncode != 0:
        warn("Docker 启动失败 — 请确认 Docker Desktop 正在运行")
        print(f"      {r.stderr.decode('gbk', errors='replace')[:200]}")
    else:
        ok("MySQL   :3307")
        ok("Redis   :6379")
        ok("Milvus  :19530")
        ok("MinIO   :9000")

    # ── Step 2: JEECG ──
    step(2, total, "JEECG ERP 系统")
    r = run("docker compose up -d", cwd=str(JEECG), capture=True)
    if r.returncode != 0:
        warn("JEECG 启动失败（平台仍可运行，但无法连接 ERP）")
    else:
        ok("JEECG 后端 :8080/jeecg-boot")
        ok("JEECG 前端 :80")
        ok("首次启动约需 2 分钟初始化，稍后可用")

    # ── Step 3: Backend ──
    step(3, total, f"平台后端 (端口 {BACKEND_PORT})")
    kill_port(BACKEND_PORT)
    time.sleep(1)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "backend")
    subprocess.Popen(
        f'start "ERP-Backend" "{PYTHON}" -m uvicorn app.main:app --host 0.0.0.0 --port {BACKEND_PORT}',
        cwd=str(ROOT / "backend"),
        env=env,
        shell=True,
    )
    ok(f"新窗口启动中 → http://localhost:{BACKEND_PORT}")

    # ── Step 4: Frontend ──
    step(4, total, f"平台前端 (端口 {FRONTEND_PORT})")
    kill_port(FRONTEND_PORT)
    # Also free nearby ports that Vite might try
    for p in [3000, 3001]:
        kill_port(p)
    time.sleep(1)

    # Write a small cmd script to launch frontend (handles esbuild + pnpm)
    launch_cmd = str(ROOT / "frontend" / "_launch.bat")
    with open(launch_cmd, "w", encoding="utf-8") as f:
        f.write(f"""@echo off
cd /d "{ROOT / 'frontend'}"
echo 正在安装依赖...
call pnpm install --silent >nul 2>&1
echo 启动 Vite 开发服务器...
call pnpm dev --port {FRONTEND_PORT} --host
""")

    subprocess.Popen(
        f'start "ERP-Frontend" cmd /c "{launch_cmd}"',
        shell=True,
    )
    ok(f"新窗口启动中 → http://localhost:{FRONTEND_PORT}")

    # ── Summary ──
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  等待 30 秒让服务就绪，然后访问：          ║")
    print("  ║                                              ║")
    print(f"  ║  平台前端    http://localhost:{FRONTEND_PORT}           ║")
    print(f"  ║  平台后端    http://localhost:{BACKEND_PORT}            ║")
    print("  ║  JEECG 管理  http://localhost:80             ║")
    print("  ║                                              ║")
    print("  ║  JEECG 账号   admin / 123456                 ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    # Wait for backend to be ready
    print("  等待后端就绪", end="", flush=True)
    for _ in range(30):
        if is_port_open(BACKEND_PORT):
            print(" ✓")
            break
        print(".", end="", flush=True)
        time.sleep(1)
    else:
        print(" (超时，请手动检查)")

    # Open browser
    print(f"  正在打开浏览器 → http://localhost:{FRONTEND_PORT}")
    time.sleep(2)
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

    print("\n  所有服务已启动。关闭此窗口不会停止服务。")
    print("  按 Enter 退出...")
    input()


if __name__ == "__main__":
    main()
