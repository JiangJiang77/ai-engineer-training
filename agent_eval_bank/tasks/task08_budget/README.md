# 题目 08：Token 预算

实现 `trim_plan`，将计划裁剪到 token 预算内。

规则：
- 每个步骤含 `estimate`（估算 token 数）。
- 按顺序保留步骤，直到加入下一步会超出 `max_tokens`。
- 返回保留步骤列表。
