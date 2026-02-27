# 题目 11：综合任务（工具调用 / 规划 / 记忆 / 鲁棒性 / 可观测性）

实现 `run_agent`，完成一个简化的 agent 执行器。

在 `src/agent.py` 中实现 `run_agent`。

功能要求：
1. **任务规划**
   - 当 query 包含 `sum` 时，生成一步：`sum` 工具，参数为 query 中出现的所有整数。
   - 当 query 包含 `echo:` 时，生成一步：`echo` 工具，参数为 `echo:` 之后的文本（去除首尾空格）。
   - 当 query 包含 `flaky` 时，生成一步：`flaky` 工具，无参数。
   - 上述规则可组合，按出现顺序执行。
2. **工具调用**
   - 使用 `tools` 字典中的函数执行工具步骤。
   - 工具返回格式：`{"status": "ok", "output": ...}`。
3. **多轮对话记忆**
   - 当 query 包含 `repeat last user` 时，直接返回最后一条 user 消息内容，不调用工具。
4. **鲁棒性**
   - 工具调用若抛异常，需重试，最多 `max_retries` 次。
   - 每次重试前调用 `sleep_fn`，延迟时间：`base_delay * 2^(attempt_index)`，attempt_index 从 0 开始。
5. **可观测性**
   - `logger` 为 list，必须追加日志：
     - 一条 `plan:` 日志，包含步骤列表（字符串化即可）。
     - 每次工具调用追加 `tool:<name> attempt:<n> status:<ok/error>`。

返回：
- 成功：`{"status": "ok", "answer": <str>}`
- 失败：`{"status": "error", "error": <str>}`
