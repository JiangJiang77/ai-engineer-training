import traceback
from typing import Any, Callable, Dict

from multi_agent.retry_manager import RetryManager


class AgentExecutor:
    def __init__(self, retry_manager: RetryManager) -> None:
        self.retry_manager = retry_manager

    def execute_agent(
        self,
        agent: Callable[[Dict[str, Any]], Dict[str, Any]],
        validator: Callable[[Dict[str, Any]], bool],
        state: Dict[str, Any],
        name: str,
    ) -> Dict[str, Any]:
        try:
            ## 调用 agent ,执行完成后，将结果数据缓存到 state增加执行日志
            result = agent(state)
            if not validator(result):
                raise ValueError("validation failed")
            state.update(result)
            if name == "review":
                state["used_fallback_review"] = False
            state["logs"].append(f"[{name}] 完成")
            state["process_logs"].append(f"{name} -> success")
            state["pending_step"] = ""
            return state
        except Exception as exc:  # noqa: BLE001
            print(f"[{name}] 发生异常: {exc}")
            traceback.print_exc()
            
            ## 发生异常则进行重试判断
            action = self.retry_manager.handle_retry(name, state, str(exc))

            ## retry: agent 重试
            if action == "retry":
                return self.execute_agent(agent, validator, state, name)

            ## fallback: 使用备用代理
            if action == "fallback":
                ## 切换成备用代理
                fallback_agent = self.retry_manager.fallback_agents[name]
                fallback_result = fallback_agent(state)
                if not validator(fallback_result):
                    ## 备用代理仍未通过，则需要用户补充信息
                    state["need_user_input"] = True
                    state["user_message"] = "备用代理仍未通过，请补充信息"
                    state["pending_step"] = name
                    return state
                state.update(fallback_result)
                if name == "review":
                    state["used_fallback_review"] = True
                state["logs"].append(f"[{name}] 备用代理完成")
                state["process_logs"].append(f"{name} -> fallback_success")
                state["pending_step"] = ""
                return state

            state["process_logs"].append(f"{name} -> ask_user")
            return state
