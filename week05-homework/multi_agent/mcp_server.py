import sys
from mcp.server.fastmcp import FastMCP

# 研究服务器
research_mcp = FastMCP("ResearchServer")


@research_mcp.tool()
def search_info(query: str) -> str:
    """搜索关于给定主题的相关信息和事实。"""
    # 模拟搜索结果
    results = {
        "AI Agent": "AI Agent 是能够感知环境、进行推理并采取行动以实现目标的智能体。它们通常由大语言模型 (LLM) 驱动，能够使用工具并进行自我迭代。",
        "MCP": "MCP (Model Context Protocol) 是一种开放协议，用于标准化 AI 模型访问数据和服务的方式。",
        "LangGraph": "LangGraph 是 LangChain 推出的一个构建循环多代理流的框架，支持精细的状态管理。",
    }
    return results.get(
        query, f"关于 '{query}' 的补充资料：这是一项处于前沿的技术趋势。"
    )


# 风格服务器
style_mcp = FastMCP("StyleServer")


@style_mcp.tool()
def get_style_guide(style_name: str) -> str:
    """获取指定文章风格的写作指南。"""
    guides = {
        "科普": "用通俗易懂的语言解释专业术语，多用比喻，保持趣味性。",
        "专业": "用语严谨，使用行业标准术语，结构化表达，强调逻辑和数据。",
        "新闻": "倒金字塔结构，先说核心结论，语言客观中立。",
    }
    return guides.get(style_name, "通用指南：内容原创，逻辑自洽，排版整洁。")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mcp_server.py [research|style]")
        sys.exit(1)

    server_type = sys.argv[1]
    if server_type == "research":
        research_mcp.run(transport="stdio")
    elif server_type == "style":
        style_mcp.run(transport="stdio")
    else:
        print(f"Unknown server type: {server_type}")
        sys.exit(1)
