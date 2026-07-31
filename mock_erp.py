"""
Mock ERP Server — responds to JEECG-compatible REST API calls.
Run: python mock_erp.py
"""
import json, uuid, time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Mock ERP (JEECG Compatible)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory storage
tokens: dict[str, dict] = {}
orgs: list[dict] = []
approval_flows: list[dict] = []
module_configs: list[dict] = []


class LoginReq(BaseModel):
    username: str = "admin"
    password: str = "123456"


@app.post("/sys/login")
async def login(req: LoginReq):
    if req.username == "admin" and req.password == "123456":
        token = str(uuid.uuid4())
        tokens[token] = {"username": req.username, "created": time.time()}
        return {"success": True, "result": {"token": token, "userInfo": {"username": req.username, "realname": "管理员"}}}
    raise HTTPException(401, "用户名或密码错误")


def verify_token(request: Request):
    auth = request.headers.get("X-Access-Token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if auth not in tokens:
        raise HTTPException(401, "Token无效或已过期")


@app.get("/health")
async def health():
    return {"status": "UP", "timestamp": time.time(), "services": {"database": "OK", "redis": "OK"}}


@app.post("/api/org")
async def create_org(request: Request):
    verify_token(request)
    body = await request.json()
    org_id = f"ORG-{len(orgs)+1:04d}"
    org = {"id": org_id, "name": body.get("name", ""), "code": body.get("code", ""), "parent_code": body.get("parent_code", ""), "node_type": body.get("node_type", "department"), "status": "active", "created_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    orgs.append(org)
    return {"success": True, "result": org}


@app.post("/api/org/batch")
async def batch_create_org(request: Request):
    verify_token(request)
    body = await request.json()
    rows = body.get("rows", [])
    created = []
    for row in rows:
        org_id = f"ORG-{len(orgs)+1:04d}"
        org = {"id": org_id, "name": row.get("name", ""), "code": row.get("code", ""), "status": "active"}
        orgs.append(org)
        created.append(org)
    return {"success": True, "result": {"imported": len(created), "failed": 0}}


@app.post("/api/approval_flow")
async def create_flow(request: Request):
    verify_token(request)
    body = await request.json()
    f_id = f"FLOW-{len(approval_flows)+1:04d}"
    flow = {"id": f_id, "name": body.get("name", ""), "steps": body.get("steps", 3), "status": "active"}
    approval_flows.append(flow)
    return {"success": True, "result": flow}


@app.post("/api/approval_flow/batch")
async def batch_create_flow(request: Request):
    verify_token(request)
    body = await request.json()
    rows = body.get("rows", [])
    created = []
    for row in rows:
        f_id = f"FLOW-{len(approval_flows)+1:04d}"
        flow = {"id": f_id, "name": row.get("name", ""), "steps": 3, "status": "active"}
        approval_flows.append(flow)
        created.append(flow)
    return {"success": True, "result": {"imported": len(created), "failed": 0}}


@app.post("/api/module_config")
async def config_module(request: Request):
    verify_token(request)
    body = await request.json()
    m_id = f"MOD-{len(module_configs)+1:04d}"
    config = {"id": m_id, "module_name": body.get("module_name", ""), "settings": body.get("settings", {}), "status": "configured"}
    module_configs.append(config)
    return {"success": True, "result": config}


@app.post("/api/module_config/batch")
async def batch_config_module(request: Request):
    verify_token(request)
    body = await request.json()
    rows = body.get("rows", [])
    created = []
    for row in rows:
        m_id = f"MOD-{len(module_configs)+1:04d}"
        config = {"id": m_id, "module_name": row.get("module_name", ""), "status": "configured"}
        module_configs.append(config)
        created.append(config)
    return {"success": True, "result": {"imported": len(created), "failed": 0}}


@app.get("/api/stats")
async def stats():
    return {"orgs": len(orgs), "flows": len(approval_flows), "modules": len(module_configs), "active_tokens": len(tokens)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
