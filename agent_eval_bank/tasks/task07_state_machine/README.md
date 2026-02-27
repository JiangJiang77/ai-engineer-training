# 题目 07：Agent 状态机

实现简单的 agent 生命周期 `transition`。

状态：`idle`、`planning`、`executing`、`failed`、`done`

事件：
- `plan`：`idle -> planning`
- `execute`：`planning -> executing`
- `succeed`：`executing -> done`
- `error`：`planning/executing -> failed`
- `reset`：`failed/done -> idle`

非法转换应抛出 `ValueError`。
