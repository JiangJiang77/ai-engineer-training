"""
# 最简单的 FastAPI + MCP 示例
"""

from __future__ import annotations

import argparse
import sys


def run_simple_example() -> None:
    # 最简单的 FastAPI + MCP 示例

    from fastapi import FastAPI
    from fastapi_mcp import FastApiMCP
    import nest_asyncio

    nest_asyncio.apply()

    # Your existing FastAPI app
    app = FastAPI()

    # Add MCP server to your FastAPI app
    mcp = FastApiMCP(
        app,
        name="My API MCP",
        describe_all_responses=True,     # 在工具描述中包含所有可能的响应模式
        describe_full_response_schema=True  # 在工具描述中包含完整的 JSON 模式
    )

    # Mount the MCP server to your app
    mcp.mount()

    # Run your app as usual
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)


def run_separate_apps_example(serve: str) -> None:
    # 与原始 FastAPI 应用分开部署
    from fastapi import FastAPI
    from fastapi_mcp import FastApiMCP

    # 您的 API 应用
    api_app = FastAPI()
    # ... 在 api_app 上定义您的 API 端点 ...

    # 一个单独的 MCP 服务器应用
    mcp_app = FastAPI()

    # 从 API 应用创建 MCP 服务器
    mcp = FastApiMCP(api_app)

    # 将 MCP 服务器挂载到单独的应用
    mcp.mount(mcp_app)

    # 现在您可以分别运行两个应用：
    # uvicorn main:api_app --host api-host --port 8001
    # uvicorn main:mcp_app --host mcp-host --port 8000

    import uvicorn

    if serve == "api":
        uvicorn.run(api_app, host="0.0.0.0", port=8001)
    elif serve == "mcp":
        uvicorn.run(mcp_app, host="0.0.0.0", port=8000)
    else:
        print("在分开部署示例中，serve 需为 api 或 mcp。", file=sys.stderr)
        sys.exit(2)


def run_user_info_example() -> None:
    # MCP 示例

    from fastapi import FastAPI, Path
    from fastapi_mcp import FastApiMCP
    import nest_asyncio

    nest_asyncio.apply()

    # Your existing FastAPI app
    app = FastAPI()

    # # (不推荐) 自动生成的 operation_id（类似于 "read_user_users__user_id__get"）
    # @app.get("/users/{user_id}")
    # async def read_user(user_id: int):
    #     return {"user_id": user_id}

    # 显式 operation_id（工具将被命名为 "get_user_info"）
    @app.get(
        "/users/{user_id}",
        operation_id="get_user_info",
        summary="获取用户信息",
        description="根据用户ID获取用户的详细信息",
        response_description="包含用户基本信息的JSON对象")
    async def read_user(
        user_id: int = Path(..., description="用户的唯一数字标识符，必须是正整数", example=123)
    ):
        return {"user_id": user_id}

    # Add MCP server to your FastAPI app
    mcp = FastApiMCP(
        app,
        name="My API MCP",
        describe_all_responses=True,     # 在工具描述中包含所有可能的响应模式
        describe_full_response_schema=True,  # 在工具描述中包含完整的 JSON 模式
    )

    # Mount the MCP server to your app
    mcp.mount()

    # Run your app as usual
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)


CLIENT_CONFIG_JSON = """\
# 客户端配置

{
  "mcpServers": {
    "my-api-mcp": {
      "url": "http://localhost:8000/mcp",
      "alwaysAllow": [],
      "disabled": false
    }
  }
}

{
  "mcpServers": {
    "my-api-mcp-proxy": {
      "command": "/Full/Path/To/Your/Executable/mcp-proxy",
      "args": ["<http://127.0.0.1:8000/mcp>"]
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FastAPI + MCP 示例集合")
    parser.add_argument(
        "--example",
        choices=["simple", "separate", "user_info"],
        default="simple",
        help="选择要运行的示例",
    )
    parser.add_argument(
        "--serve",
        choices=["api", "mcp"],
        help="分开部署示例下选择启动 api 还是 mcp",
    )
    parser.add_argument(
        "--show-client-config",
        action="store_true",
        help="打印客户端配置示例",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.show_client_config:
        print(CLIENT_CONFIG_JSON)

    if args.example == "simple":
        run_simple_example()
    elif args.example == "separate":
        if not args.serve:
            print("分开部署示例需要 --serve api 或 --serve mcp。", file=sys.stderr)
            sys.exit(2)
        run_separate_apps_example(args.serve)
    else:
        run_user_info_example()


if __name__ == "__main__":
    main()
