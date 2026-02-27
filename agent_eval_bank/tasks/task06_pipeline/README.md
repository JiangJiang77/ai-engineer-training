# 题目 06：流水线执行器

实现 `run_pipeline`，按顺序执行工具步骤列表。

规则：
- 每个步骤：`{"tool": <name>, "args": {...}}`
- `tools` 是工具函数字典，返回：
  - `{"status": "ok", "output": ...}` 或 `{"status": "error", "error": "..."}`
- 出现错误立即停止。
- 返回字典：
  - `status`："ok" 或 "error"
  - `results`：成功步骤输出列表
  - `logs`：每步日志字符串列表
