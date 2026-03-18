from pathlib import Path
from typing import Optional

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from multi_agent.config import SETTINGS
from multi_agent.graph import build_graph
from multi_agent.log import get_logger, setup_logging
from multi_agent.state import WriterState, build_initial_state

logger = get_logger(__name__)



def write_report(state: WriterState, report_path: Path) -> None:
    lines = [
        "# 多代理文章编写系统执行报告",
        "",
        f"## 任务主题：{state['topic']}",
        "",
        "## 1. 最终文章",
        "",
        state.get("final_article", "生成失败"),
        "",
        "## 2. 执行过程",
        "",
    ]

    lines.extend([f"- {log}" for log in state.get("logs", [])])

    lines.extend(
        [
            "",
            "## 3. 异常处理日志",
            "",
        ]
    )

    exception_logs = state.get("exception_logs", [])
    if exception_logs:
        lines.extend([f"- {log}" for log in exception_logs])
    else:
        lines.append("- 无")

    lines.extend(
        [
            "",
            "## 4. 代理产物",
            "",
            "### 研究结果",
            str(state.get("research", {})),
            "",
            "### 审核结果",
            str(state.get("review", {})),
            "",
            "### 审核历史",
            str(state.get("review_history", [])),
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


def _strip_interrupt(result: dict) -> tuple[WriterState, list]:
    interrupts = result.get("__interrupt__", [])
    state = {k: v for k, v in result.items() if k != "__interrupt__"}
    return state, interrupts


def _prompt_user(interrupt_payload: dict) -> dict | None:
    message = str(interrupt_payload.get("message", "需要补充信息"))
    current_topic = str(interrupt_payload.get("topic", ""))
    print(f"\n[System] {message}")
    print(f"[System] 当前主题: {current_topic}")
    try:
        user_topic = input("请输入更具体的主题（留空保留原主题）: ").strip()
    except EOFError:
        return None
    return {"topic": user_topic}


def run(
    topic: str,
    thread_id: str,
    checkpoint_db: str,
) -> WriterState:
    db_path = Path(checkpoint_db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn_string = str(db_path.resolve())
    config = {"configurable": {"thread_id": thread_id}}
    logger.debug("run start: topic=%s, thread_id=%s, checkpoint_db=%s", topic, thread_id, checkpoint_db)

    with SqliteSaver.from_conn_string(conn_string) as checkpointer:
        graph = build_graph(checkpointer=checkpointer)
        pending_input = build_initial_state(topic=topic)

        while True:
            result = graph.invoke(pending_input, config=config)
            state, interrupts = _strip_interrupt(result)
            ## 没有中断，则返回执行结果
            if not interrupts:
                logger.debug("run finished without interrupt")
                return state

            interrupt_payload = interrupts[0].value
            if not isinstance(interrupt_payload, dict):
                interrupt_payload = {"message": str(interrupt_payload)}
            #把中断信息展示给用户并获取回复
            user_reply = _prompt_user(interrupt_payload)
            if user_reply is None:
                state["logs"].append("[System] 非交互模式，终止当前轮执行")
                logger.debug("run stopped: non-interactive mode")
                return state
            #把用户回复包装为“恢复命令”，作为下一轮 graph.invoke 的输入，让图从中断点继续执行。
            pending_input = Command(resume=user_reply)
            logger.debug("run resumed from interrupt with user_reply")


def print_result(final_state: WriterState) -> None:
    print("\n========================")
    print("Agent 协作记录")
    print("========================")
    for item in final_state["logs"]:
        print(item)

    print("\n========================")
    print("最终文章")
    print("========================")
    print(final_state.get("final_article", ""))

    print("\n========================")
    print("异常日志")
    print("========================")
    if final_state["exception_logs"]:
        for item in final_state["exception_logs"]:
            print(item)
    else:
        print("无")


def _run_once(
    topic: str,
    thread_id: str,
    checkpoint_db: str,
) -> WriterState:
    final_state = run(
        topic=topic,
        thread_id=thread_id,
        checkpoint_db=checkpoint_db,
    )
    print_result(final_state)
    report_path = Path(__file__).with_name(f"report_{thread_id}.md")
    write_report(final_state, report_path)
    print(f"\n报告已写入: {report_path}")
    return final_state


def interactive_chat(
    checkpoint_db: str,
    base_thread_id: str,
    initial_topic: Optional[str] = None,
) -> None:
    print("进入多轮交互模式。输入主题开始一轮写作。")
    print("命令: /quit 退出")
    round_id = 1

    if initial_topic:
        thread_id = f"{base_thread_id}-{round_id}"
        print(f"\n[Round {round_id}] thread_id={thread_id}")
        _run_once(
            topic=initial_topic,
            thread_id=thread_id,
            checkpoint_db=checkpoint_db,
        )
        round_id += 1

    while True:
        try:
            user_input = input("\nUser> ").strip()
        except EOFError:
            print("\n收到 EOF，结束会话。")
            break

        if not user_input:
            continue
        if user_input in {"/quit", "quit", "exit"}:
            break

        thread_id = f"{base_thread_id}-{round_id}"
        print(f"[Round {round_id}] thread_id={thread_id}")
        _run_once(
            topic=user_input,
            thread_id=thread_id,
            checkpoint_db=checkpoint_db,
        )
        round_id += 1


def main() -> None:
    setup_logging(SETTINGS.log_level)
    logger.debug("app start with LOG_LEVEL=%s", SETTINGS.log_level)
    default_topic = SETTINGS.default_topic
    base_thread_id = SETTINGS.base_thread_id
    checkpoint_db = SETTINGS.checkpoint_db

    interactive_chat(
        checkpoint_db=checkpoint_db,
        base_thread_id=base_thread_id,
        initial_topic=default_topic,
    )


if __name__ == "__main__":
    main()
