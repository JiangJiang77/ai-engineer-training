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
    # 评审阶段: initial -> recheck
    review_stage: str
    # 当前阶段返工轮次
    review_round: int
    # 每个阶段最大返工轮次
    max_review_round: int
    # 审核历史
    review_history: List[Dict[str, Any]]
    # 当前待落实的修改要求
    review_requirements: List[str]

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
        "review_stage": "initial",
        "review_round": 0,
        "max_review_round": 2,
        "review_history": [],
        "review_requirements": [],
    }
