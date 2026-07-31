# ReAct-based LLM agent loop with Function Calling, context management, and memory
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# ─── Message types (OpenAI-compatible) ────────────────────────

def _system(content: str) -> dict: return {"role": "system", "content": content}
def _user(content: str) -> dict: return {"role": "user", "content": content}
def _assistant(content: str, tool_calls: list = None) -> dict:
    msg = {"role": "assistant", "content": content or ""}
    if tool_calls: msg["tool_calls"] = tool_calls
    return msg
def _tool(call_id: str, content: str) -> dict:
    return {"role": "tool", "tool_call_id": call_id, "content": content}


# ─── LLM API client ───────────────────────────────────────────

async def _chat_completion(
    messages: list[dict],
    model: str,
    base_url: str,
    api_key: str,
    tools: list[dict] = None,
    response_format: dict = None,
    temperature: float = 0.1,
    max_tokens: int = 16384,
) -> dict:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {
        "model": model, "messages": messages,
        "temperature": temperature, "max_tokens": max_tokens,
    }
    if tools: payload["tools"] = tools
    if response_format: payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]


# ─── Context helpers ──────────────────────────────────────────

def _estimate_tokens(messages: list[dict]) -> int:
    """Rough token estimate: 1 char ≈ 0.5 tokens for Chinese, 0.25 for English."""
    total = 0
    for m in messages:
        content = m.get("content", "") or ""
        total += len(content) * 0.4
    return int(total)


def _compact_messages(messages: list[dict], max_tokens: int = 8000) -> list[dict]:
    """Keep system prompt + last N messages that fit within token budget."""
    if _estimate_tokens(messages) <= max_tokens:
        return messages

    system_msgs = [m for m in messages if m["role"] == "system"]
    other_msgs = [m for m in messages if m["role"] != "system"]

    # Summarize old tool results if too many
    compacted = list(system_msgs)
    token_budget = max_tokens - _estimate_tokens(system_msgs) - 500

    # Keep recent messages, summarize older ones
    kept = []
    for m in reversed(other_msgs):
        kept_tokens = _estimate_tokens(kept)
        if kept_tokens + _estimate_tokens([m]) > token_budget:
            break
        kept.insert(0, m)

    compacted.extend(kept)
    if len(compacted) < len(messages):
        compacted.insert(len(system_msgs), _assistant(f"[上下文已压缩，省略了{len(messages) - len(compacted)}条消息]"))
    return compacted


# ─── Main ReAct Agent Loop ────────────────────────────────────

async def agent_loop(
    system_prompt: str,
    user_task: str,
    output_schema: dict,
    tools: list[dict],
    tool_executor: callable,
    model: str = "",
    api_config: dict = None,
    max_iterations: int = 50,
    max_context_tokens: int = 12000,
) -> dict[str, Any]:
    """
    ReAct agent loop: Reason → Act → Observe → Repeat.

    The LLM can call tools autonomously. The loop continues until:
    - The LLM produces a final JSON output (no more tool calls)
    - Max iterations reached → force output
    - Context overflows → auto-compact
    """
    settings = get_settings()
    base_url = settings.llm_base_url
    api_key = settings.llm_api_key
    use_model = model or settings.llm_default_model

    if api_config:
        base_url = api_config.get("base_url", base_url)
        api_key = api_config.get("api_key", api_key)
        use_model = api_config.get("model_name", use_model)

    if not api_key or not api_key.strip():
        logger.warning("No API key, returning mock")
        return _mock_response(output_schema)

    is_deepseek = "deepseek" in base_url.lower()

    messages: list[dict] = [
        _system(system_prompt),
        _user(user_task),
    ]

    tool_names = [t["function"]["name"] for t in tools] if tools else []
    logger.info("Agent loop start: model=%s, tools=%s, deepseek=%s", use_model, tool_names, is_deepseek)

    for iteration in range(max_iterations):
        # Auto-compact if context grows too large
        if _estimate_tokens(messages) > max_context_tokens:
            logger.info("Compacting context at iteration %d", iteration)
            messages = _compact_messages(messages, max_context_tokens)

        is_final = iteration >= max_iterations - 2

        # Build payload
        payload_tools = tools if tools and not is_final else None
        payload_format = None
        if is_final and output_schema:
            if is_deepseek:
                payload_format = {"type": "json_object"}
            else:
                payload_format = {"type": "json_schema", "json_schema": {"name": "output", "strict": True, "schema": output_schema}}

        try:
            msg = await _chat_completion(
                messages=messages, model=use_model, base_url=base_url, api_key=api_key,
                tools=payload_tools, response_format=payload_format,
            )
        except Exception as exc:
            logger.exception("LLM API error at iteration %d", iteration)
            if iteration == 0:
                return _mock_response(output_schema)
            break

        # Check for tool calls
        tool_calls = msg.get("tool_calls", [])
        if tool_calls:
            # Record assistant message with tool calls
            messages.append(_assistant(msg.get("content"), tool_calls))

            # Execute each tool and record results
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                try:
                    func_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    func_args = {}

                logger.info("Tool: %s(%s...)", func_name, json.dumps(func_args, ensure_ascii=False)[:100])
                result = await tool_executor(func_name, func_args)
                result_str = json.dumps(result, ensure_ascii=False)

                # Truncate large tool results
                if len(result_str) > 2000:
                    result_str = result_str[:2000] + f"...[truncated, {len(result_str)} chars total]"

                messages.append(_tool(tc["id"], result_str))
            continue

        # No tool calls → LLM produced final answer
        content = msg.get("content", "")
        logger.info("Agent loop complete at iteration %d, response length=%d", iteration, len(content))

        # Parse JSON from response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            return {"raw_output": content}

    # Max iterations exhausted — force output
    logger.warning("Max iterations reached, forcing output")
    try:
        final_msg = await _chat_completion(
            messages=messages + [_user("请现在立即输出JSON结果，不要调用任何工具。")],
            model=use_model, base_url=base_url, api_key=api_key,
            response_format={"type": "json_object"} if is_deepseek else None,
        )
        return json.loads(final_msg.get("content", "{}"))
    except Exception:
        return _mock_response(output_schema)


# ─── Backward-compatible simple call ──────────────────────────

async def call_llm(
    system_prompt: str, user_message: str, output_schema: dict,
    model: str = None, api_config: dict = None,
) -> dict[str, Any]:
    return await agent_loop(
        system_prompt=system_prompt, user_task=user_message,
        output_schema=output_schema, tools=[], tool_executor=lambda n, a: {},
        model=model, api_config=api_config, max_iterations=1,
    )


# ─── Schema & Mock helpers ────────────────────────────────────

def build_json_schema(pydantic_model: type) -> dict:
    return _simplify_schema(pydantic_model.model_json_schema())


def _simplify_schema(schema: dict) -> dict:
    result: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
    props = schema.get("properties", {})
    required = schema.get("required", [])
    for key, prop in props.items():
        if "$ref" in prop:
            result["properties"][key] = _resolve_ref(prop["$ref"], schema)
        elif prop.get("type") == "array":
            items = prop.get("items", {})
            if "$ref" in items:
                result["properties"][key] = {"type": "array", "items": _resolve_ref(items["$ref"], schema)}
            else:
                result["properties"][key] = {"type": "array", "items": items}
        elif "anyOf" in prop:
            non_null = [o for o in prop["anyOf"] if o.get("type") != "null"]
            if non_null:
                opt = non_null[0]
                if "$ref" in opt:
                    resolved = _resolve_ref(opt["$ref"], schema)
                    resolved["type"] = [o.get("type") for o in prop["anyOf"] if o.get("type")]
                    result["properties"][key] = resolved
                else:
                    result["properties"][key] = dict(opt)
        else:
            result["properties"][key] = {k: v for k, v in prop.items() if k != "title"}
    result["required"] = required
    return result


def _resolve_ref(ref: str, root_schema: dict) -> dict:
    parts = ref.split("/")
    current = root_schema
    for part in parts[1:]:
        current = current.get(part, {})
    if current.get("type") == "object":
        return _simplify_schema(current)
    return dict(current)


def _mock_response(schema: dict) -> dict[str, Any]:
    props = schema.get("properties", {})
    result: dict[str, Any] = {}
    for key, prop in props.items():
        result[key] = _default_for_prop(prop)
    return result


def _default_for_prop(prop: dict) -> Any:
    prop_type = prop.get("type", "string")
    if prop_type == "array": return []
    if prop_type == "object": return {}
    if prop_type == "integer": return 0
    if prop_type == "number": return 0.0
    if prop_type == "boolean": return False
    if "anyOf" in prop:
        has_null = any(opt.get("type") == "null" for opt in prop.get("anyOf", []))
        if has_null: return None
        for opt in prop.get("anyOf", []):
            if opt.get("type") == "null": continue
            if "$ref" in opt: return {}
            return _default_for_prop(opt)
        return None
    return ""
