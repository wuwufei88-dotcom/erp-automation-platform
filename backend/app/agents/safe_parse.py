from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def safe_parse(output: dict, model_cls: type[T]) -> T:
    """Try Pydantic validation first. If it fails, use model_construct to skip validation."""
    try:
        return model_cls(**output)
    except Exception:
        pass

    cleaned: dict = {}
    for field_name, field_info in model_cls.model_fields.items():
        value = output.get(field_name)
        annotation = field_info.annotation

        if value is None:
            cleaned[field_name] = field_info.default if field_info.default is not None else _empty_for_type(annotation)
            continue

        try:
            if _is_list_type(annotation):
                cleaned[field_name] = _coerce_list(value, field_name, _get_item_type(annotation))
            elif _is_dict_type(annotation):
                cleaned[field_name] = value if isinstance(value, dict) else {}
            elif _is_int_type(annotation):
                cleaned[field_name] = _coerce_int(value)
            elif _is_float_type(annotation):
                cleaned[field_name] = _coerce_float(value)
            elif _is_str_type(annotation):
                cleaned[field_name] = _coerce_str(value)
            elif _is_bool_type(annotation):
                cleaned[field_name] = bool(value)
            else:
                cleaned[field_name] = value
        except Exception:
            cleaned[field_name] = _empty_for_type(annotation)

    return model_cls.model_construct(**cleaned)


def _empty_for_type(annotation) -> any:
    if _is_list_type(annotation): return []
    if _is_dict_type(annotation): return {}
    if _is_int_type(annotation): return 0
    if _is_float_type(annotation): return 0.0
    if _is_bool_type(annotation): return False
    return ""


def _is_list_type(annotation) -> bool:
    origin = getattr(annotation, "__origin__", None)
    return origin is list


def _is_dict_type(annotation) -> bool:
    origin = getattr(annotation, "__origin__", None)
    return origin is dict


def _is_int_type(annotation) -> bool:
    return annotation is int


def _is_float_type(annotation) -> bool:
    return annotation is float


def _is_str_type(annotation) -> bool:
    return annotation is str


def _is_bool_type(annotation) -> bool:
    return annotation is bool


def _coerce_int(value) -> int:
    if isinstance(value, int): return value
    if isinstance(value, float): return int(value)
    if isinstance(value, bool): return 1 if value else 0
    if isinstance(value, str):
        try: return int(value)
        except ValueError: return len(value)
    if isinstance(value, list): return len(value)
    return 0


def _coerce_float(value) -> float:
    if isinstance(value, float): return value
    if isinstance(value, int): return float(value)
    if isinstance(value, str):
        try: return float(value)
        except ValueError: return 0.0
    return 0.0


def _coerce_str(value) -> str:
    if isinstance(value, str): return value
    if isinstance(value, dict):
        parts = [f"{k}: {v}" for k, v in value.items()]
        return "; ".join(parts) if parts else str(value)
    if isinstance(value, list):
        return "、".join(str(v) for v in value)
    return str(value)


def _coerce_list(value, field_name: str, item_type=None) -> list:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        if "、" in value:
            items = [v.strip() for v in value.split("、") if v.strip()]
        elif "," in value:
            items = [v.strip() for v in value.split(",") if v.strip()]
        elif "\n" in value:
            items = [v.strip() for v in value.split("\n") if v.strip()]
        else:
            items = [value]
    elif isinstance(value, (int, float)):
        items = [value]
    elif value is None:
        items = []
    else:
        items = [str(value)]

    # If items are dicts and field expects model objects, construct them
    if item_type and issubclass(item_type, BaseModel):
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(item_type.model_construct(**item))
            elif isinstance(item, item_type):
                result.append(item)
            else:
                result.append(item)
        return result
    return items


def _get_item_type(annotation) -> type | None:
    """Extract the item type from a list[X] annotation."""
    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        args = getattr(annotation, "__args__", ())
        if args and args[0] is not type(None):
            return args[0]
    return None
