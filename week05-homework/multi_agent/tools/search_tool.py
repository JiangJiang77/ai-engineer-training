import asyncio
import json
from typing import Dict, List

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from multi_agent.config import SETTINGS
from multi_agent.log import get_logger

logger = get_logger(__name__)
REQUIRED_FIELDS = ("title", "summary", "source")


def _normalize_record(item: Dict[str, object]) -> Dict[str, str]:
    return {
        "title": str(item.get("title", "")),
        "summary": str(item.get("summary", "")),
        "source": str(item.get("source", "")),
    }


def _try_parse_record(item: object) -> Dict[str, str] | None:
    if isinstance(item, dict) and all(field in item for field in REQUIRED_FIELDS):
        return _normalize_record(item)

    # MCP streamable-http may wrap tool payload as {'type':'text','text':'{...json...}'}
    if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
        text = item["text"]
        try:
            parsed = json.loads(text)
        except Exception:
            return None
        if isinstance(parsed, dict) and all(field in parsed for field in REQUIRED_FIELDS):
            return _normalize_record(parsed)
    return None


async def _search_via_mcp(topic: str, max_results: int = 3) -> List[Dict[str, str]]:
    mcp_url = SETTINGS.mcp_research_url
    logger.debug("search start: topic=%s, max_results=%s, mcp_url=%s", topic, max_results, mcp_url)
    client = MultiServerMCPClient(
        {
            "research_server": {
                "url": mcp_url,
                "transport": "streamable-http",
            }
        }
    )

    async with client.session("research_server") as session:
        tools = await load_mcp_tools(session)
        tool = next((item for item in tools if item.name == "tavily_search"), None)
        if tool is None:
            raise RuntimeError("tavily_search tool not found on MCP server")

        result = await tool.ainvoke({"query": topic, "max_results": max_results})

    if not isinstance(result, list):
        raise RuntimeError("unexpected MCP response from tavily_search")

    normalized: List[Dict[str, str]] = []
    for item in result:
        record = _try_parse_record(item)
        if record is not None:
            normalized.append(record)

    if not normalized:
        raise RuntimeError("unexpected MCP payload shape: expected records with title/summary/source")
    logger.debug("search done: topic=%s, result_count=%s", topic, len(normalized))
    return normalized


def search_tool(topic: str) -> List[Dict[str, str]]:
    try:
        return asyncio.run(_search_via_mcp(topic=topic, max_results=3))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"MCP tavily search failed: {exc}") from exc
