
## LangGraph `thread_id` 设置与生效规则

`thread_id` 是 LangGraph 持久化线程的主键。只有在启用 `checkpointer` 时才会生效。

### 1. 如何设置

1. 编译图时启用 checkpointer（例如 `InMemorySaver`）：

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
compiled_graph = workflow.compile(checkpointer=checkpointer)
```

2. 调用图时传入 `configurable.thread_id`：

```python
config = {"configurable": {"thread_id": "user-42"}}
compiled_graph.invoke({"messages": [...]}, config=config)
# 或 compiled_graph.stream(..., config=config)
```

### 2. 生效规则

1. 相同 `thread_id`：复用同一线程状态（会话记忆累积）。
2. 不同 `thread_id`：状态隔离。
3. `checkpoint_id`：用于指定历史检查点（回放/分叉）。
4. `checkpoint_ns`：用于命名空间（常见于子图场景）。

如果启用了 checkpointer 但未传 `thread_id`，通常会触发配置校验错误（提示需要 `thread_id/checkpoint_ns/checkpoint_id` 之一）。

### 3. 查看方式

可以基于同一个 `config` 查询线程状态与历史：

```python
state = compiled_graph.get_state(config)
history = list(compiled_graph.get_state_history(config))
```

- `get_state(config)`: 查看当前线程最新状态。
- `get_state_history(config)`: 查看该线程历史 checkpoint。

### 4. 官方文档

- LangGraph Persistence（Python）
  https://docs.langchain.com/oss/python/langgraph/persistence
- BaseCheckpointSaver（`thread_id`/`checkpoint_ns`/`checkpoint_id` 配置说明）
  https://reference.langchain.com/python/langgraph.checkpoint/base/BaseCheckpointSaver
- LangGraph Platform Threads
  https://docs.langchain.com/langgraph-platform/use-threads

## LangGraph `stream_mode=updates` 和 `stream_mode=values` 区别

### 1. 核心区别

- `updates`：返回每一步的状态增量（本步新增/变更字段）。
- `values`：返回每一步的完整状态快照（当前全量 state）。

### 2. 适用场景

- `updates`：更轻量，适合做事件监听、UI 增量渲染、日志追踪。
- `values`：更直观，适合调试全局状态演进，但数据量更大。

### 3. 最小示例

```python
# 增量模式：每步只看变更
for event in graph.stream(inputs, stream_mode="updates"):
    print(event)

# 全量模式：每步都看完整 state
for state in graph.stream(inputs, stream_mode="values"):
    print(state)
```

### 4. 输出理解

假设初始 state 为 `{"topic": "ice cream"}`：

1. 第一步节点更新 `topic`。
- `updates`：只看到 `topic` 的变更。
- `values`：看到当前完整 state（包含最新 `topic`）。

2. 第二步节点新增 `joke`。
- `updates`：只看到 `joke` 的变更。
- `values`：看到完整 state（`topic + joke`）。
