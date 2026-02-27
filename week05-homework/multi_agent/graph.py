from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from .agents import State, research_node, writing_node, review_node, polishing_node, llm


def create_workflow(mcp_tools: list):
    # 绑定工具到研究节点专用的 LLM
    llm_with_tools = llm.bind_tools(mcp_tools)

    workflow = StateGraph(State)

    # 定义包含参数传递的节点包装器
    async def call_research(state: State):
        return await research_node(state, llm_with_tools)

    # 添加节点
    workflow.add_node("research", call_research)
    workflow.add_node("mcp_tools", ToolNode(mcp_tools))
    workflow.add_node("writing", writing_node)
    workflow.add_node("review", review_node)
    workflow.add_node("polishing", polishing_node)

    # 定义边和逻辑
    workflow.add_edge(START, "research")

    # 研究后的跳转逻辑：
    def after_research_condition(state: State) -> Literal["mcp_tools", "writing"]:
        last_msg = state["messages"][-1]
        # 如果有工具调用且不是刚刚执行完工具（工具消息后面没跟新的内容）
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "mcp_tools"
        # 如果已经有了研究结果或最后一条消息是工具结果，则进入写作
        if state.get("research_results") or last_msg.type == "tool":
            return "writing"
        return "mcp_tools"  # 默认 fallback

    workflow.add_conditional_edges(
        "research",
        after_research_condition,
        {"mcp_tools": "mcp_tools", "writing": "writing"},
    )

    workflow.add_edge("mcp_tools", "research")
    workflow.add_edge("writing", "review")

    # 审核后的路由（实现三级重试逻辑）
    def review_router(state: State) -> Literal["polishing", "retry", "failure"]:
        comments = state.get("review_comments", "").lower()
        retry_count = state.get("retry_count", 0)

        if "通过" in comments and "不通过" not in comments:
            return "polishing"

        if retry_count < 3:  # 三级重试限制
            return "retry"

        return "failure"

    async def retry_node(state: State):
        count = state.get("retry_count", 0) + 1
        log = f"[System] 触发重试逻辑，当前重试次数: {count}"
        print(log)
        return {"retry_count": count, "logs": [log]}

    workflow.add_node("retry_manager", retry_node)

    workflow.add_conditional_edges(
        "review",
        review_router,
        {"polishing": "polishing", "retry": "retry_manager", "failure": END},
    )

    # 重试后回到哪个节点？根据当前步骤决定
    def after_retry_router(state: State) -> str:
        step = state.get("current_step", "research")
        return step

    workflow.add_conditional_edges(
        "retry_manager",
        after_retry_router,
        {
            "research": "research",
            "writing": "writing",
            "review": "review",
            "polishing": "polishing",
        },
    )

    workflow.add_edge("polishing", END)

    return workflow.compile()
