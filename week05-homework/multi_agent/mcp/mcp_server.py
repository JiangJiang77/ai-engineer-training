import os
import json
from pathlib import Path
from typing import Dict, List

from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

mcp_server = FastMCP("research-mcp")

CACHE_FILE = Path(
    os.getenv(
        "TAVILY_CACHE_FILE",
        str(Path(__file__).resolve().parent / "tavily_cache.json"),
    )
)
REQUIRED_FIELDS = ("title", "summary", "source")


def _cache_key(query: str, max_results: int) -> str:
    return f"{query.strip()}||{max_results}"


def _normalize_record(item: Dict[str, object]) -> Dict[str, str]:
    return {
        "title": str(item.get("title", "")),
        "summary": str(item.get("summary", "")),
        "source": str(item.get("source", "")),
    }


def _normalize_records(items: List[Dict[str, object]]) -> List[Dict[str, str]]:
    return [_normalize_record(item) for item in items]


def _load_cache() -> Dict[str, List[Dict[str, str]]]:
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    normalized: Dict[str, List[Dict[str, str]]] = {}
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, list):
            normalized_items = [
                _normalize_record(item)
                for item in value
                if isinstance(item, dict)
            ]
            normalized[key] = normalized_items
    return normalized


def _save_cache(cache: Dict[str, List[Dict[str, str]]]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@mcp_server.tool()
def tavily_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search web results via Tavily and return compact structured data."""
    key = _cache_key(query=query, max_results=max_results)
    cache = _load_cache()
    cached_results = cache.get(key)
    if isinstance(cached_results, list) and cached_results:
        return _normalize_records(cached_results)  # type: ignore[arg-type]

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is required (cache miss)")
    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
    )

    results: List[Dict[str, object]] = []
    for item in response.get("results", []):
        results.append(
            {
                "title": item.get("title", ""),
                "summary": item.get("content", ""),
                "source": item.get("url", ""),
            }
        )

    normalized_results = _normalize_records(results)
    cache[key] = normalized_results
    _save_cache(cache)
    return normalized_results


if __name__ == "__main__":
    has_key = bool(os.getenv("TAVILY_API_KEY"))
    print(f"[mcp_server] TAVILY_API_KEY loaded: {has_key}")
    mcp_server.run(transport="streamable-http")
