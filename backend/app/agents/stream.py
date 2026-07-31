# True streaming agent loop — token-level SSE from LLM API
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def agent_loop_stream(
    system_prompt: str,
    user_task: str,
    output_schema: dict,
    tools: list[dict],
    tool_executor,
    model: str = "",
    api_config: dict = None,
    max_iterations: int = 50,
) -> AsyncGenerator[dict, None]:
    """ReAct agent loop with TRUE token-level streaming from the LLM API."""
    settings = get_settings()
    base_url = settings.llm_base_url
    api_key = settings.llm_api_key
    use_model = model or settings.llm_default_model

    if api_config:
        base_url = api_config.get("base_url", base_url)
        api_key = api_config.get("api_key", api_key)
        use_model = api_config.get("model_name", use_model)

    if not api_key or not api_key.strip():
        yield {"type": "warning", "content": "No API key configured"}
        yield {"type": "output", "content": {}}
        return

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    tool_names = [t["function"]["name"] for t in tools] if tools else []
    yield {"type": "start", "model": use_model, "tools": tool_names}

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_task},
    ]

    async with httpx.AsyncClient(timeout=180) as client:
        for iteration in range(max_iterations):
            is_final = iteration >= max_iterations - 2

            payload: dict = {
                "model": use_model, "messages": messages,
                "temperature": 0.1, "max_tokens": 4096,
                "stream": True,  # ← KEY: enable SSE streaming
            }
            if tools and not is_final:
                payload["tools"] = tools

            yield {"type": "think", "iteration": iteration, "content": f"Thinking... (step {iteration + 1}/{max_iterations})"}

            try:
                # Stream the API response token by token
                async with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as resp:
                    resp.raise_for_status()

                    content_buf = ""
                    tool_call_buf: dict[int, dict] = {}  # index → {id, name, arguments_str}
                    finish_reason = None

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")

                        # Stream text content token by token
                        if delta.get("content"):
                            token = delta["content"]
                            content_buf += token
                            yield {"type": "token", "content": token}

                        # Accumulate tool calls from streaming deltas
                        if delta.get("tool_calls"):
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in tool_call_buf:
                                    tool_call_buf[idx] = {"id": tc.get("id", ""), "name": "", "arguments": ""}
                                if tc.get("id"):
                                    tool_call_buf[idx]["id"] = tc["id"]
                                if tc.get("function", {}).get("name"):
                                    tool_call_buf[idx]["name"] = tc["function"]["name"]
                                if tc.get("function", {}).get("arguments"):
                                    tool_call_buf[idx]["arguments"] += tc["function"]["arguments"]

                    # Process completed tool calls
                    if tool_call_buf:
                        tool_calls_list = []
                        for idx in sorted(tool_call_buf.keys()):
                            tc = tool_call_buf[idx]
                            if tc["name"] and tc["id"]:
                                tool_calls_list.append({
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                                })

                        if tool_calls_list:
                            # Record assistant message
                            messages.append({"role": "assistant", "content": content_buf or None, "tool_calls": tool_calls_list})

                            for tc in tool_calls_list:
                                func_name = tc["function"]["name"]
                                try:
                                    func_args = json.loads(tc["function"]["arguments"])
                                except json.JSONDecodeError:
                                    func_args = {}

                                yield {"type": "tool_call", "name": func_name, "args": func_args}

                                try:
                                    result = await tool_executor(func_name, func_args)
                                except Exception as e:
                                    result = {"success": False, "error": str(e)}

                                yield {"type": "tool_result", "name": func_name, "result": result}

                                result_str = json.dumps(result, ensure_ascii=False)
                                if len(result_str) > 2000:
                                    result_str = result_str[:2000] + "...[truncated]"

                                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result_str})
                            continue

                    # No tool calls — final output
                    if content_buf:
                        try:
                            parsed = json.loads(content_buf)
                        except json.JSONDecodeError:
                            import re
                            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content_buf, re.DOTALL)
                            if match:
                                try:
                                    parsed = json.loads(match.group(1))
                                except json.JSONDecodeError:
                                    parsed = {"raw_output": content_buf}
                            else:
                                parsed = {"raw_output": content_buf}
                        yield {"type": "output", "content": parsed}
                        return

            except Exception as exc:
                logger.exception("LLM error at iteration %d", iteration)
                yield {"type": "error", "content": str(exc)}
                if iteration == 0:
                    return
                break

    yield {"type": "error", "content": "Max iterations reached"}
    yield {"type": "output", "content": {}}


# ─── Web Search Tool ───────────────────────────────────────────

async def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web using DuckDuckGo (free, no API key needed)."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")})
        return {"success": True, "data": {"results": results, "source": "DuckDuckGo"}}
    except ImportError:
        return {"success": False, "error": "web_search 不可用: pip install ddgs"}
    except Exception as e:
        logger.warning("Web search failed: %s, using fallback", e)
        return await _web_search_fallback(query, max_results)


async def _web_search_fallback(query: str, max_results: int = 5) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            from html.parser import HTMLParser

            class ResultParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.results = []
                    self.current = {}
                    self.in_result = False

                def handle_starttag(self, tag, attrs):
                    attrs_dict = dict(attrs)
                    if tag == "a" and "result__a" in attrs_dict.get("class", ""):
                        self.in_result = True
                        self.current = {"title": "", "url": attrs_dict.get("href", ""), "snippet": ""}

                def handle_data(self, data):
                    if self.in_result and not self.current.get("title"):
                        self.current["title"] = data.strip()

                def handle_endtag(self, tag):
                    if tag == "a" and self.in_result:
                        if self.current.get("title"):
                            self.results.append(self.current)
                        self.in_result = False
                        self.current = {}

            parser = ResultParser()
            parser.feed(resp.text)
            return {"success": True, "data": {"results": parser.results[:max_results], "source": "DuckDuckGo (fallback)"}}
    except Exception as e:
        return {"success": False, "error": f"Web search unavailable: {e}"}
