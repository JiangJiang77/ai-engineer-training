# 题目 04：鲁棒重试

实现带指数退避的 `retry_call`。

规则：
- 最多尝试 `max_attempts` 次。
- 失败后在下一次尝试前 sleep。
- sleep 时间：`base_delay * 2^(attempt_index)`，attempt_index 从 0 开始。
- 如果全部失败，重新抛出最后一个异常。
