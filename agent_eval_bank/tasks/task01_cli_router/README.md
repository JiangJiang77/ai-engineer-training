# 题目 01：CLI 工具路由

构建一个供 agent 使用的小型工具路由器，要求：
- 只允许调用白名单内的工具。
- 使用 Python 执行 `tools/` 目录下的脚本。
- 返回 stdout 字符串，去除尾部空白。

在 `src/router.py` 中实现 `route_tool`。

期望行为：
- 未知工具抛出 `ValueError`。
- 使用 `sys.executable` 执行脚本，避免 shell 注入。
