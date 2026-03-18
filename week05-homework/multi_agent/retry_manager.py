from typing import Any, Callable, Dict

MAX_RETRY = 2


class RetryManager:
    def __init__(self, fallback_agents: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]):
        self.fallback_agents = fallback_agents

    def handle_retry(self, agent_name: str, state: Dict[str, Any], error: str) -> str:
        retry_count = state["retry_count"].get(agent_name, 0)
        state["exception_logs"].append(f"{agent_name} failed: {error}")

        ## 重试次数小于最大重试次数，则重试
        if retry_count < MAX_RETRY:
            state["retry_count"][agent_name] = retry_count + 1
            state["exception_logs"].append(
                f"{agent_name} retry ({retry_count + 1}/{MAX_RETRY})"
            )
            return "retry"

        ## 重试次数大于等于最大重试次数，则使用备用代理
        if agent_name in self.fallback_agents:
            state["exception_logs"].append(f"{agent_name} switch to fallback")
            return "fallback"

        state["need_user_input"] = True
        state["user_message"] = "需要补充更具体的主题"
        state["pending_step"] = agent_name
        return "ask_user"
