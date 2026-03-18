from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from multi_agent.agents import (
    fallback_review_agent,
    polishing_agent,
    research_agent,
    review_agent,
    writing_agent,
    validate_polishing,
    validate_research,
    validate_review,
    validate_writing,
)
from multi_agent.executor import AgentExecutor
from multi_agent.log import get_logger
from multi_agent.retry_manager import RetryManager
from multi_agent.state import WriterState

logger = get_logger(__name__)

retry_manager = RetryManager(fallback_agents={"review": fallback_review_agent})
executor = AgentExecutor(retry_manager=retry_manager)


def _route_from_start(state: WriterState) -> Literal["research", "write", "review", "polish"]:
    if state.get("pending_step"):
        target = state["pending_step"]
        logger.debug("edge START -> %s (pending_step)", target)
        return target  # type: ignore[return-value]
    logger.debug("edge START -> research (default)")
    return "research"


def _route_next_or_wait(next_step: str):
    def _router(state: WriterState) -> Literal["wait_user", "research", "write", "review", "polish"]:
        if state.get("need_user_input"):
            logger.debug("edge route -> wait_user (need_user_input=True)")
            return "wait_user"
        logger.debug("edge route -> %s (need_user_input=False)", next_step)
        return next_step  

    return _router


def _route_after_polish(state: WriterState) -> Literal["wait_user", "end"]:
    if state.get("need_user_input"):
        logger.debug("edge polish -> wait_user")
        return "wait_user"
    logger.debug("edge polish -> END")
    return "end"

def _route_after_review(state: WriterState) -> Literal["wait_user", "polish", "end"]:
    if state.get("need_user_input"):
        logger.debug("edge review -> wait_user")
        return "wait_user"
    if state.get("used_fallback_review"):
        logger.debug("edge review -> END (used_fallback_review=True)")
        return "end"
    logger.debug("edge review -> polish")
    return "polish"


def research_node(state: WriterState) -> WriterState:
    logger.debug("node research start: topic=%s", state.get("topic"))
    state["logs"].append("[Research Agent] 搜索资料")
    out = executor.execute_agent(research_agent, validate_research, state, "research")
    logger.debug("node research end: has_sources=%s", bool(out.get("research", {}).get("sources")))
    return out


def writing_node(state: WriterState) -> WriterState:
    logger.debug("node write start")
    state["logs"].append("[Writing Agent] 生成初稿")
    out = executor.execute_agent(writing_agent, validate_writing, state, "write")
    logger.debug("node write end: draft_len=%s", len(out.get("draft", "")))
    return out


def review_node(state: WriterState) -> WriterState:
    logger.debug("node review start")
    state["logs"].append("[Review Agent] 审核内容")
    out = executor.execute_agent(review_agent, validate_review, state, "review")
    logger.debug(
        "node review end: score=%s, used_fallback_review=%s",
        out.get("review", {}).get("score"),
        out.get("used_fallback_review"),
    )
    return out


def polishing_node(state: WriterState) -> WriterState:
    logger.debug("node polish start")
    state["logs"].append("[Polishing Agent] 润色定稿")
    out = executor.execute_agent(polishing_agent, validate_polishing, state, "polish")
    logger.debug("node polish end: final_len=%s", len(out.get("final_article", "")))
    return out


def wait_user_node(state: WriterState) -> WriterState:
    logger.debug("node wait_user start")
    if not state["logs"] or state["logs"][-1] != "[System] 等待用户补充信息":
        state["logs"].append("[System] 等待用户补充信息")
    payload = {
        "message": state.get("user_message", "需要补充信息"),
        "topic": state.get("topic", ""),
    }
    user_reply = interrupt(payload)
    if isinstance(user_reply, dict):
        topic = str(user_reply.get("topic", "")).strip()
        if topic:
            state["topic"] = topic
    elif isinstance(user_reply, str) and user_reply.strip():
        state["topic"] = user_reply.strip()
    state["need_user_input"] = False
    state["user_message"] = ""
    state["logs"].append("[System] 已接收用户输入，继续执行")
    logger.debug("node wait_user end: topic=%s", state.get("topic"))
    return state


def build_graph(checkpointer):
    logger.debug("building graph")
    builder = StateGraph(WriterState)

    builder.add_node("research", research_node)
    builder.add_node("write", writing_node)
    builder.add_node("review", review_node)
    builder.add_node("polish", polishing_node)
    builder.add_node("wait_user", wait_user_node)

    builder.add_conditional_edges(
        START,
        _route_from_start,
        {
            "research": "research",
            "write": "write",
            "review": "review",
            "polish": "polish",
        },
    )
    builder.add_conditional_edges("research", _route_next_or_wait("write"))
    builder.add_conditional_edges("write", _route_next_or_wait("review"))
    builder.add_conditional_edges(
        "review",
        _route_after_review,
        {"wait_user": "wait_user", "polish": "polish", "end": END},
    )
    builder.add_conditional_edges(
        "polish",
        _route_after_polish,
        {"wait_user": "wait_user", "end": END},
    )

    builder.add_conditional_edges(
        "wait_user",
        _route_from_start,
        {
            "research": "research",
            "write": "write",
            "review": "review",
            "polish": "polish",
        },
    )

    return builder.compile(checkpointer=checkpointer)
