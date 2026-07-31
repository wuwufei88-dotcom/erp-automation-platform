from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import ApiConfig, ErpConfig
from app.schemas import ApiConfigCreate, ApiConfigRead, ApiConfigUpdate, ErpConfigCreate, ErpConfigRead, ErpConfigUpdate
from app.tools.erp_provider import list_providers, get_provider, load_providers

router = APIRouter()

PRESET_PROVIDERS = [
    {"display_name": "DeepSeek V4 Pro", "provider": "DeepSeek", "base_url": "https://api.deepseek.com", "model_name": "deepseek-v4-pro", "is_preset": 1},
    {"display_name": "DeepSeek V4 Flash", "provider": "DeepSeek", "base_url": "https://api.deepseek.com", "model_name": "deepseek-v4-flash", "is_preset": 1},
    {"display_name": "OpenAI GPT-4o", "provider": "OpenAI", "base_url": "https://api.openai.com/v1", "model_name": "gpt-4o", "is_preset": 1},
    {"display_name": "OpenAI GPT-4o-mini", "provider": "OpenAI", "base_url": "https://api.openai.com/v1", "model_name": "gpt-4o-mini", "is_preset": 1},
    {"display_name": "Anthropic Claude Sonnet 4", "provider": "Anthropic", "base_url": "https://api.anthropic.com", "model_name": "claude-sonnet-4-20250514", "is_preset": 1},
    {"display_name": "Anthropic Claude Opus 4", "provider": "Anthropic", "base_url": "https://api.anthropic.com", "model_name": "claude-opus-4-20250514", "is_preset": 1},
    {"display_name": "OpenRouter (多模型)", "provider": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "model_name": "openai/gpt-4o", "is_preset": 1},
    {"display_name": "Groq (高速推理)", "provider": "Groq", "base_url": "https://api.groq.com/openai/v1", "model_name": "llama-3.3-70b-versatile", "is_preset": 1},
    {"display_name": "Mistral", "provider": "Mistral", "base_url": "https://api.mistral.ai/v1", "model_name": "mistral-large-latest", "is_preset": 1},
    {"display_name": "硅基流动 (SiliconFlow)", "provider": "SiliconFlow", "base_url": "https://api.siliconflow.cn/v1", "model_name": "deepseek-ai/DeepSeek-V3", "is_preset": 1},
    {"display_name": "阿里百炼 (Qwen)", "provider": "Alibaba", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model_name": "qwen-max", "is_preset": 1},
    {"display_name": "Moonshot (Kimi)", "provider": "Moonshot", "base_url": "https://api.moonshot.cn/v1", "model_name": "moonshot-v1-8k", "is_preset": 1},
    {"display_name": "Ollama (本地)", "provider": "Ollama", "base_url": "http://localhost:11434/v1", "model_name": "llama3", "is_preset": 1},
    {"display_name": "vLLM (本地)", "provider": "vLLM", "base_url": "http://localhost:8000/v1", "model_name": "default", "is_preset": 1},
]


@router.get("/api-configs", response_model=list[ApiConfigRead])
async def list_api_configs(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ApiConfig).order_by(ApiConfig.id.asc()))).scalars().all()
    return [ApiConfigRead.model_validate(r) for r in rows]


@router.post("/api-configs", response_model=ApiConfigRead, status_code=201)
async def create_api_config(body: ApiConfigCreate, db: AsyncSession = Depends(get_db)):
    config = ApiConfig(**body.model_dump(), is_preset=0)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.put("/api-configs/{config_id}", response_model=ApiConfigRead)
async def update_api_config(config_id: int, body: ApiConfigUpdate, db: AsyncSession = Depends(get_db)):
    config = (await db.execute(select(ApiConfig).where(ApiConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="API config not found")
    if config.is_preset:
        if body.api_key is not None:
            config.api_key = body.api_key
            await db.commit()
            await db.refresh(config)
            return config
        raise HTTPException(status_code=400, detail="Preset providers can only update api_key. To change other fields, create a copy.")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(config, key, val)
    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/api-configs/{config_id}", status_code=204)
async def delete_api_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = (await db.execute(select(ApiConfig).where(ApiConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="API config not found")
    if config.is_preset:
        raise HTTPException(status_code=400, detail="Cannot delete preset providers")
    await db.delete(config)
    await db.commit()


@router.post("/api-configs/seed-presets")
async def seed_presets(db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(func.count(ApiConfig.id)))).scalar() or 0
    if existing > 0:
        return {"message": f"{existing} configs already exist, skipping seed"}
    for preset in PRESET_PROVIDERS:
        db.add(ApiConfig(**preset, api_key=""))
    await db.commit()
    return {"message": f"Seeded {len(PRESET_PROVIDERS)} preset providers"}


# ─── ERP Config Endpoints ──────────────────────────────────────

def _build_erp_presets() -> list[dict]:
    """Generate ERP presets from YAML provider configs (excludes Custom)."""
    presets = []
    for p in list_providers():
        if p["provider"] == "Custom":
            continue  # Custom is handled via "添加 ERP" button
        cfg = get_provider(p["provider"]) or {}
        auth = cfg.get("auth", p) if isinstance(cfg.get("auth"), dict) else {}
        entity_paths = cfg.get("entity_paths", {})
        auth_type = auth.get("type", p.get("auth_type", "none")) if isinstance(auth, dict) else "none"
        token_url = auth.get("token_url", "")
        token_header = auth.get("token_header", "Authorization: Bearer")
        # Build preset entry
        preset: dict = {
            "display_name": p["name"],
            "provider": p["provider"],
            "base_url": "" if p["provider"] == "Custom" else "",
            "auth_type": auth_type,
            "token_url": token_url,
            "token_header": token_header,
            "is_preset": 1,
        }
        # Add default credentials for known dev instances
        if p["provider"] == "JEECG":
            preset["base_url"] = "http://localhost:8080/jeecg-boot"
            preset["credential_key"] = "admin"
            preset["credential_secret"] = "123456"
        elif p["provider"] == "Odoo":
            preset["base_url"] = "http://localhost:8069"
            preset["credential_key"] = "odoo"
            preset["credential_secret"] = ""
        elif p["provider"] == "ERPNext":
            preset["base_url"] = "http://localhost:8000"
            preset["credential_key"] = "Administrator"
            preset["credential_secret"] = ""
        elif p["provider"] == "YonSuite":
            preset["base_url"] = "https://openapi.yonyoucloud.com"
        elif p["provider"] == "SAP":
            preset["base_url"] = "https://my-s4hana-api.s4hana.ondemand.com"
        elif p["provider"] == "Dynamics365":
            preset["base_url"] = "https://api.businesscentral.dynamics.com/v2.0"
        presets.append(preset)
    return presets


ERP_PRESETS = _build_erp_presets()


@router.get("/erp-providers")
async def list_erp_providers_endpoint():
    """List all available ERP provider templates loaded from YAML configs."""
    return list_providers()


@router.post("/erp-providers/reload")
async def reload_erp_providers():
    """Hot-reload ERP provider configs from YAML files without restarting."""
    global ERP_PRESETS
    load_providers()
    ERP_PRESETS = _build_erp_presets()
    providers = list_providers()
    return {"message": f"Reloaded {len(providers)} ERP providers", "providers": [p["name"] for p in providers]}


@router.get("/erp-configs", response_model=list[ErpConfigRead])
async def list_erp_configs(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ErpConfig).order_by(ErpConfig.id.asc()))).scalars().all()
    return [ErpConfigRead.model_validate(r) for r in rows]


@router.post("/erp-configs", response_model=ErpConfigRead, status_code=201)
async def create_erp_config(body: ErpConfigCreate, db: AsyncSession = Depends(get_db)):
    config = ErpConfig(**body.model_dump(), is_preset=0)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.put("/erp-configs/{config_id}", response_model=ErpConfigRead)
async def update_erp_config(config_id: int, body: ErpConfigUpdate, db: AsyncSession = Depends(get_db)):
    config = (await db.execute(select(ErpConfig).where(ErpConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="ERP config not found")
    if config.is_preset:
        allowed = {"credential_key", "credential_secret", "static_token", "tenant_id", "display_name"}
        for key, val in body.model_dump(exclude_unset=True).items():
            if key in allowed:
                setattr(config, key, val)
        await db.commit()
        await db.refresh(config)
        return config
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(config, key, val)
    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/erp-configs/{config_id}", status_code=204)
async def delete_erp_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = (await db.execute(select(ErpConfig).where(ErpConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="ERP config not found")
    if config.is_preset:
        raise HTTPException(status_code=400, detail="Cannot delete preset providers")
    await db.delete(config)
    await db.commit()


@router.post("/erp-configs/seed-presets")
async def seed_erp_presets(db: AsyncSession = Depends(get_db), force: bool = False):
    if not force:
        existing = (await db.execute(select(func.count(ErpConfig.id)))).scalar() or 0
        if existing > 0:
            return {"message": f"{existing} ERP configs already exist, skipping seed"}
    else:
        # Force: delete all existing presets AND custom configs, then re-seed presets
        await db.execute(ErpConfig.__table__.delete().where(ErpConfig.is_preset == 1))
        await db.execute(ErpConfig.__table__.delete().where(ErpConfig.is_preset == 0))
        await db.commit()
        # Reset auto-increment to keep IDs starting from 1
        await db.execute(text("ALTER TABLE erp_configs AUTO_INCREMENT = 1"))
        await db.commit()
    for preset in ERP_PRESETS:
        db.add(ErpConfig(**preset))
    await db.commit()
    return {"message": f"Seeded {len(ERP_PRESETS)} ERP preset providers"}


@router.post("/erp-configs/{config_id}/reset")
async def reset_erp_config(config_id: int, db: AsyncSession = Depends(get_db)):
    config = (await db.execute(select(ErpConfig).where(ErpConfig.id == config_id))).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="ERP config not found")
    if not config.is_preset:
        raise HTTPException(status_code=400, detail="Only preset providers can be reset")

    # Find matching preset from YAML
    provider_name = config.provider
    matching_preset = None
    for preset in ERP_PRESETS:
        if preset["provider"] == provider_name:
            matching_preset = preset
            break

    if not matching_preset:
        raise HTTPException(status_code=404, detail=f"No preset found for provider: {provider_name}")

    # Reset fields to YAML defaults (keep same ID and preset status)
    for key, val in matching_preset.items():
        if key not in ("id", "is_preset"):
            setattr(config, key, val)
    await db.commit()
    await db.refresh(config)
    return {"message": f"Reset {provider_name} to defaults", "id": config.id}
