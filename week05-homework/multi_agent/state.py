from typing import Any, Dict, List, TypedDict


class WriterState(TypedDict):
    # 主题
    topic: str
    # 风格
    style: str
    # 长度
    length: int
    # 研究结果
    research: Dict[str, Any]
    # 初稿
    draft: str
    # 审核结果
    review: Dict[str, Any]
    # 最终文章
    final_article: str
    # 重试次数
    retry_count: Dict[str, int]
    # 日志
    logs: List[str]
    # 处理日志
    process_logs: List[str]
    # 异常日志
    exception_logs: List[str]
    # 是否需要用户输入
    need_user_input: bool
    # 用户输入
    user_message: str
    # 当前步骤
    pending_step: str
    # review 是否使用过 fallback
    used_fallback_review: bool

def build_initial_state(topic: str) -> WriterState:
    return {
        "topic": topic,
        "style": "专业科普",
        "length": 1200,
        "research": {},
        "draft": "",
        "review": {},
        "final_article": "",
        "retry_count": {},
        "logs": [],
        "process_logs": [],
        "exception_logs": [],
        "need_user_input": False,
        "user_message": "",
        "pending_step": "",
        "used_fallback_review": False,
    }
