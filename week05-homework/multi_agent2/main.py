import asyncio
import os
import sys
from typing import List
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from .graph import create_workflow
from .agents import State


async def main():
    # 配置 MCP 客户端 (参考 week05 样式)
    # 使用 python 运行本地 mcp_server.py
    server_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")

    client = MultiServerMCPClient(
        {
            "research_server": {
                "command": "python",
                "args": [server_script, "research"],
                "transport": "stdio",
            },
            "style_server": {
                "command": "python",
                "args": [server_script, "style"],
                "transport": "stdio",
            },
        }
    )

    async with client.session("research_server") as research_session, client.session(
        "style_server"
    ) as style_session:

        print("已连接到 MCP 服务器：Research & Style")

        # 加载所有工具
        research_tools = await load_mcp_tools(research_session)
        style_tools = await load_mcp_tools(style_session)
        all_tools = research_tools + style_tools

        # 创建并编译工作流
        app = create_workflow(all_tools)

        # 初始输入
        if len(sys.argv) > 1:
            user_input = sys.argv[1]
        else:
            print(
                "提示：你可以通过命令行参数指定主题，例如：python -m multi_agent.main 'AI Agent 的未来'"
            )
            user_input = input("请输入文章主题（例如 'AI Agent 的未来'）：")

        if not user_input:
            user_input = "AI Agent 的实现原理与应用"

        initial_state = {
            "messages": [{"role": "user", "content": user_input}],
            "research_results": "",
            "draft": "",
            "review_comments": "",
            "final_article": "",
            "retry_count": 0,
            "current_step": "research",
            "logs": [f"System: 开始任务 - {user_input}"],
        }

        print("\n--- 开始执行多代理文章编写流程 ---\n")

        final_result = initial_state
        async for state_values in app.astream(
            initial_state,
            config={"configurable": {"thread_id": "article_1"}},
            stream_mode="values",
        ):
            # 记录最新的完整状态
            final_result = state_values

            # 打印最新的日志（如果有）
            if "logs" in state_values and state_values["logs"]:
                print(state_values["logs"][-1])

        print("\n--- 流程执行完毕 ---\n")
        print("最终文章已生成，正在保存到 report.md...")

        # 保存到 report.md
        report_path = os.path.join(os.path.dirname(__file__), "report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 多代理文章编写系统执行报告\n\n")
            f.write(f"## 任务主题：{user_input}\n\n")
            f.write("## 1. 最终文章定稿\n\n")
            f.write(final_result.get("final_article", "生成失败"))
            f.write("\n\n---\n\n")
            f.write("## 2. 执行过程日志\n\n")
            for log in final_result.get("logs", []):
                f.write(f"- {log}\n")

            f.write("\n## 3. 代理交互细节\n\n")
            f.write(
                f"### 研究阶段结果\n{final_result.get('research_results', 'N/A')}\n\n"
            )
            f.write(f"### 初稿内容\n{final_result.get('draft', 'N/A')}\n\n")
            f.write(f"### 审核建议\n{final_result.get('review_comments', 'N/A')}\n\n")

            if final_result.get("retry_count", 0) > 0:
                f.write(
                    f"\n## 4. 异常处理日志\n\n- 触发了重试机制，总重试次数：{final_result['retry_count']}\n"
                )


if __name__ == "__main__":
    asyncio.run(main())
