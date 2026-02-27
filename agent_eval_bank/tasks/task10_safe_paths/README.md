# 题目 10：安全文件访问

实现 `safe_join`，防止路径穿越。

规则：
- 拼接 `base_dir` 和 `user_path`。
- 解析为绝对路径。
- 若解析后的路径不在 `base_dir` 内，抛出 `ValueError`。
