# Agent Eval Bank

离线题库，用于评测个人工程师在构建 AI agent 应用时的工程能力。

覆盖能力：
- 工具调用
- 任务规划
- 多轮对话记忆
- 鲁棒性与错误处理
- 可观测性（日志与可解释输出）

## 安装（uv）

```bash
uv sync
```

## 运行全部题目

```bash
python runner/run_all.py
```

## 运行单题

```bash
python runner/run_all.py --task task01_cli_router
```

## 题目结构

每题包含：
- `README.md` 需求说明
- `src/` 起始代码
- `tests/` 判题测试

## 评分

- 主指标：每题通过/失败（pytest）
- 可选：记录通过时间与迭代次数
