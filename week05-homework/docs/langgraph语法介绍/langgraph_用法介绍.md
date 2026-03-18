# LangGraph 用法介绍

## 本轮小记：State 定义与 `add_messages`

### 1) 两种 `State` 定义方式的核心区别

```python
class AgentState(TypedDict):
    intent: str
    order_id: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
```

```python
class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
```

区别重点不在 `TypedDict`，而在 `messages` 的 reducer（合并函数）：

- `operator.add`：普通列表拼接，等价于 `old + new`。
- `add_messages`：LangGraph 消息专用合并器，会做消息标准化、按 `id` 覆盖、支持删除等。

结论：对话/工具调用场景建议优先用 `add_messages`。

---

### 2) `add_messages` 具体做了什么

`add_messages(left, right)` 主要行为：

1. 统一输入：把单条消息和列表都规整为列表。
2. 标准化消息：把 tuple/dict/message 对象转换为标准消息对象。
3. 自动补 `id`：缺失 `id` 时自动生成 UUID。
4. 按 `id` 合并：
- `id` 不存在 -> 追加。
- `id` 已存在 -> 用新消息覆盖旧消息。
5. 支持删除：
- 通过 `RemoveMessage(id=...)` 删除指定消息。
- 特殊 `RemoveMessage(id="__remove_all__")` 可清空已有消息。
6. 可选格式化：支持 `format="langchain-openai"` 输出格式。

---

### 3) 最小对比例子

#### 3.1 同 ID 场景：`operator.add` vs `add_messages`

```python
from langchain_core.messages import HumanMessage
from langgraph.graph.message import add_messages
import operator

left = [HumanMessage(content="你好", id="1")]
right = [HumanMessage(content="你好，已修改", id="1")]

print(operator.add(left, right))
# [HumanMessage(id="1", content="你好"), HumanMessage(id="1", content="你好，已修改")]

print(add_messages(left, right))
# [HumanMessage(id="1", content="你好，已修改")]
```

要点：`operator.add` 会重复保留同 `id` 消息；`add_messages` 会覆盖更新。

#### 3.2 删除消息场景

```python
from langchain_core.messages import HumanMessage, RemoveMessage
from langgraph.graph.message import add_messages

left = [
    HumanMessage(content="第一条", id="1"),
    HumanMessage(content="第二条", id="2"),
]
right = [RemoveMessage(id="1")]

print(add_messages(left, right))
# [HumanMessage(id="2", content="第二条")]
```

---

### 4) 删除旧消息的应用场景

- 修正错误消息：早期写入内容错误，删除后重写。
- 控制上下文长度：裁剪历史，降低 token 成本。
- 清理中间态：移除调试信息、失败工具调用等临时消息。
- 工具失败回滚：删除错误 tool call/message，避免污染后续推理。
- 阶段切换裁剪：多阶段工作流中，清理上阶段无关上下文。

---

### 5) 实践建议

- 对 LangGraph 的 `messages` 状态，优先使用：

```python
messages: Annotated[List[AnyMessage], add_messages]
```

- 仅在你明确只需要“原样拼接”且不需要覆盖/删除语义时，再考虑 `operator.add`。
