"""ERP Provider loader — reads YAML configs from config/erp_providers/ and provides
a unified interface for ERPClient to target different ERP systems."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, dict] = {}
_PROVIDER_DIR = Path(__file__).resolve().parent.parent.parent.parent / "config" / "erp_providers"


def _find_provider_dir() -> Path:
    """Find the erp_providers config directory."""
    # Try relative to this file first: backend/app/tools/erp_provider.py → project root
    candidates = [
        _PROVIDER_DIR,
        Path(os.getcwd()) / "config" / "erp_providers",
        Path(os.getcwd()).parent / "config" / "erp_providers",
    ]
    for d in candidates:
        if d.is_dir():
            return d
    return _PROVIDER_DIR


def load_providers() -> dict[str, dict]:
    """Load all ERP provider YAML files from the config directory.
    Returns a dict keyed by provider name (lowercase)."""
    global _PROVIDERS
    provider_dir = _find_provider_dir()
    _PROVIDERS = {}

    if not provider_dir.is_dir():
        logger.warning("ERP provider directory not found: %s", provider_dir)
        return _PROVIDERS

    for yaml_file in sorted(provider_dir.glob("*.yaml")):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or "provider" not in data:
                continue
            key = data["provider"].lower()
            data["_source_file"] = str(yaml_file)
            _PROVIDERS[key] = data
            logger.info("Loaded ERP provider: %s (%s)", data["name"], key)
        except Exception as exc:
            logger.warning("Failed to load %s: %s", yaml_file, exc)

    return _PROVIDERS


def get_provider(provider_name: str) -> dict | None:
    """Get a single provider config by name (case-insensitive)."""
    if not _PROVIDERS:
        load_providers()
    return _PROVIDERS.get(provider_name.lower())


def list_providers() -> list[dict]:
    """List all available provider summaries (for API/admin UI)."""
    if not _PROVIDERS:
        load_providers()
    result = []
    for key, cfg in _PROVIDERS.items():
        auth = cfg.get("auth", {})
        result.append({
            "provider": cfg["provider"],
            "name": cfg["name"],
            "description": cfg.get("description", ""),
            "website": cfg.get("website", ""),
            "api_style": cfg.get("api_style", "rest"),
            "auth_type": auth.get("type", "none"),
            "token_url": auth.get("token_url", ""),
            "token_header": auth.get("token_header", "Authorization: Bearer"),
            "credential_label": auth.get("credential_label", ""),
            "secret_label": auth.get("secret_label", ""),
            "default_base_url": cfg.get("default_base_url", ""),
            "source_file": cfg.get("_source_file", ""),
        })
    return result


def build_entity_paths(provider_name: str) -> dict[str, str]:
    """Get the entity path mapping for a provider."""
    cfg = get_provider(provider_name)
    if not cfg:
        return {}
    return cfg.get("entity_paths", {})


def build_response_mapping(provider_name: str) -> dict:
    """Get the response parsing configuration for a provider."""
    cfg = get_provider(provider_name)
    if not cfg:
        return {}
    return cfg.get("response", {})


def get_tenant_isolation(provider_name: str) -> dict:
    """Get the tenant isolation config for a provider."""
    cfg = get_provider(provider_name)
    if not cfg:
        return {}
    return cfg.get("tenant_isolation", {})


# Auto-load on import
load_providers()
