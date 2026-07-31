from __future__ import annotations

from typing import Any


def robust_parse(output: dict, normalize_fn: callable = None) -> dict:
    """General normalizer for LLM JSON output. Handles common formatting issues."""
    result = dict(output)

    for key, value in result.items():
        result[key] = _normalize_value(value)

    if normalize_fn:
        result = normalize_fn(result)

    return result


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_value(v) for v in value]
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return value
    if value is None:
        return value
    return str(value)


def fix_list_field(output: dict, key: str, item_defaults: dict = None) -> list:
    """Ensure a field is a list of dicts with required keys."""
    val = output.get(key, [])
    if isinstance(val, str):
        val = [val]
    if not isinstance(val, list):
        val = [val] if val else []
    result = []
    for item in val:
        if isinstance(item, str):
            item = {"name": item, "description": item} if key != "ambiguities" else item
        if isinstance(item, dict) and item_defaults:
            for k, v in item_defaults.items():
                item.setdefault(k, v)
        result.append(item)
    output[key] = result
    return result


def fix_dict_field(output: dict, key: str) -> dict:
    """Ensure a field is a dict."""
    val = output.get(key, {})
    if isinstance(val, list):
        mapping = {}
        for item in val:
            if isinstance(item, dict):
                src = item.get("source", item.get("from", str(len(mapping))))
                tgt = item.get("target", item.get("to", str(item)))
                mapping[str(src)] = str(tgt)
        output[key] = mapping
        return mapping
    if not isinstance(val, dict):
        output[key] = {}
        return {}
    return val


def fix_int_field(output: dict, key: str, default: int = 0) -> int:
    val = output.get(key, default)
    if val is None:
        output[key] = default
        return default
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        output[key] = int(val)
        return int(val)
    if isinstance(val, str):
        try:
            output[key] = int(val)
            return int(val)
        except ValueError:
            output[key] = default
            return default
    output[key] = default
    return default


def fix_str_field(output: dict, key: str, default: str = "") -> str:
    val = output.get(key, default)
    if isinstance(val, dict):
        parts = [f"{k}: {v}" for k, v in val.items()]
        result = "; ".join(parts) if parts else str(val)
        output[key] = result
        return result
    if not isinstance(val, str):
        output[key] = str(val) if val else default
        return output[key]
    return val
