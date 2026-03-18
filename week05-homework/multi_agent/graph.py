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
REVIEW_STAGE_ORDER = ("initial", "recheck")


def _normalize_review_stage(stage: str) -> str:
    alias = {"peer": "initial", "editor": "initial", "final": "recheck"}
    mapped = alias.get(stage, stage)
    if mapped not in REVIEW_STAGE_ORDER:
        return "initial"
    return mapped


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

def _route_after_review(state: WriterState) -> Literal["wait_user", "write", "review", "polish"]:
    if state.get("need_user_input"):
        logger.debug("edge review -> wait_user")
        return "wait_user"

    review = state.get("review", {})
    if not review.get("passed", False):
        logger.debug("edge review -> write (review not passed)")
        return "write"

    stage = _normalize_review_stage(str(state.get("review_stage", "initial")))
    if stage == "recheck":
        logger.debug("edge review -> polish (recheck stage passed)")
        return "polish"

    logger.debug("edge review -> review (advance to next stage)")
    return "review"


def _next_stage(stage: str) -> str:
    try:
        idx = REVIEW_STAGE_ORDER.index(_normalize_review_stage(stage))
    except ValueError:
        return "initial"
    if idx >= len(REVIEW_STAGE_ORDER) - 1:
        return "recheck"
    return REVIEW_STAGE_ORDER[idx + 1]


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
    if out.get("need_user_input"):
        return out

    review = out.get("review", {})
    stage = _normalize_review_stage(str(review.get("stage", out.get("review_stage", "initial"))))
    passed = bool(review.get("passed", False))
    score = float(review.get("score", 0.0))
    issues = review.get("issues", [])
    requirements = review.get("requirements", [])
    if not isinstance(issues, list):
        issues = [str(issues)]
    if not isinstance(requirements, list):
        requirements = [str(requirements)]

    review["stage"] = stage
    review["issues"] = issues
    review["requirements"] = requirements
    review["score"] = score
    review["passed"] = passed
    out["review"] = review

    if passed:
        out["review_round"] = 0
        out["review_requirements"] = []
        next_stage = _next_stage(stage)
        out["review_stage"] = next_stage
        if stage == "recheck":
            out["logs"].append("[review] 复审通过，进入润色")
        else:
            out["logs"].append(f"[review] {stage} 通过，进入 {next_stage}")
    else:
        next_round = int(out.get("review_round", 0)) + 1
        out["review_round"] = next_round
        out["review_stage"] = stage
        out["review_requirements"] = requirements
        out["logs"].append(f"[review] {stage} 未通过，进入第 {next_round} 轮改写")
        if next_round >= int(out.get("max_review_round", 2)):
            out["need_user_input"] = True
            out["user_message"] = f"{stage} 阶段已达到最大返工轮次，请补充更具体信息后继续。"
            out["pending_step"] = "write"
            out["logs"].append("[review] 已达到返工上限，等待用户补充")

    history = out.get("review_history", [])
    history.append(
        {
            "stage": stage,
            "round": int(out.get("review_round", 0)),
            "score": score,
            "passed": passed,
            "issues": issues,
            "requirements": requirements,
        }
    )
    out["review_history"] = history

    logger.debug(
        "node review end: score=%s, stage=%s, passed=%s",
        out.get("review", {}).get("score"),
        out.get("review_stage"),
        out.get("review", {}).get("passed"),
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
        {"wait_user": "wait_user", "write": "write", "review": "review", "polish": "polish"},
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
