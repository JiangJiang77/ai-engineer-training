# LangGraph Streaming 官方文档中文翻译

> 原文主题：LangGraph Streaming（流式输出）
> 说明：本文为你提供的官方文档内容中文翻译版，代码示例基本保留原样，文字说明翻译为中文。

## Streaming

LangGraph 实现了一套流式系统，用于在运行时输出实时更新。流式输出对于提升基于 LLM 的应用响应体验非常关键。通过在完整响应生成前就逐步展示结果，流式输出可以显著改善用户体验（UX），尤其是在 LLM 存在延迟时。

## 快速开始

### 基础用法

LangGraph 图对象提供 [`stream`](https://reference.langchain.com/python/langgraph/pregel/#langgraph.pregel.Pregel.stream)（同步）和 [`astream`](https://reference.langchain.com/python/langgraph/pregel/#langgraph.pregel.Pregel.astream)（异步）方法，以迭代器形式产出流式结果。你可以传入一个或多个 [stream mode](#stream-modes) 来控制接收的数据类型。

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["updates", "custom"],
    version="v2",
):
    if chunk["type"] == "updates":
        for node_name, state in chunk["data"].items():
            print(f"Node {node_name} updated: {state}")
    elif chunk["type"] == "custom":
        print(f"Status: {chunk['data']['status']}")
```

```shell
Status: thinking of a joke...
Node generate_joke updated: {'joke': 'Why did the ice cream go to school? To get a sundae education!'}
```

### 流式输出格式（v2）

> 需要 LangGraph >= 1.1。本文示例均使用 `version="v2"`。

向 `stream()` 或 `astream()` 传入 `version="v2"` 可获得统一输出格式。每个 chunk 都是一个 `StreamPart` 字典，无论你使用哪种 stream mode、是否组合多种 mode、是否包含 subgraph，格式都一致：

```python
{
    "type": "values" | "updates" | "messages" | "custom" | "checkpoints" | "tasks" | "debug",
    "ns": (),           # 命名空间元组；子图事件时会填充
    "data": ...,        # 实际负载（具体类型取决于 stream mode）
}
```

每种 mode 都有对应的 `TypedDict` 类型（可从 `langgraph.types` 导入）：
- `ValuesStreamPart`
- `UpdatesStreamPart`
- `MessagesStreamPart`
- `CustomStreamPart`
- `CheckpointStreamPart`
- `TasksStreamPart`
- `DebugStreamPart`

联合类型 `StreamPart` 以 `part["type"]` 作为判别字段（discriminated union），编辑器与类型检查器可自动收窄类型。

v1（默认）中，输出格式会随配置变化：
- 单 mode：直接返回原始数据
- 多 mode：返回 `(mode, data)` 元组
- 子图：返回 `(namespace, data)` 元组

v2 中始终是同一结构。

```python
for chunk in graph.stream(inputs, stream_mode="updates", version="v2"):
    print(chunk["type"])  # "updates"
    print(chunk["ns"])    # ()
    print(chunk["data"])  # {"node_name": {"key": "value"}}
```

### Stream modes

`stream` / `astream` 可接收以下 mode（单个或列表）：

- `values`：每步后的完整 state
- `updates`：每步的 state 增量更新（同一步多个更新会分别流出）
- `messages`：LLM token 与 metadata 的二元组
- `custom`：通过 `get_stream_writer()` 主动写出的自定义数据
- `checkpoints`：检查点事件（需要 checkpointer）
- `tasks`：任务开始/结束与结果/错误（需要 checkpointer）
- `debug`：最全调试信息（包含 checkpoints 与 tasks 及额外元数据）

## 图状态流式输出

可使用 `updates` 与 `values` 观察图执行状态：

- `updates`：流式输出节点返回的状态增量
- `values`：流式输出每步完整状态

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
  topic: str
  joke: str


def refine_topic(state: State):
    return {"topic": state["topic"] + " and cats"}


def generate_joke(state: State):
    return {"joke": f"This is a joke about {state['topic']}"}

graph = (
  StateGraph(State)
  .add_node(refine_topic)
  .add_node(generate_joke)
  .add_edge(START, "refine_topic")
  .add_edge("refine_topic", "generate_joke")
  .add_edge("generate_joke", END)
  .compile()
)
```

`updates` 示例：

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="updates",
    version="v2",
):
    if chunk["type"] == "updates":
        for node_name, state in chunk["data"].items():
            print(f"Node `{node_name}` updated: {state}")
```

`values` 示例：

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="values",
    version="v2",
):
    if chunk["type"] == "values":
        print(f"topic: {chunk['data']['topic']}, joke: {chunk['data']['joke']}")
```

## LLM token 流式输出

使用 `messages` mode 可以从图中的任意位置按 token 流式获取 LLM 输出（节点、工具、子图、任务均可）。

`messages` mode 的输出是 `(message_chunk, metadata)`：
- `message_chunk`：token 或消息片段
- `metadata`：节点、调用上下文等元信息

> 若你的 LLM 不是 LangChain 集成模型，可用 `custom` mode 实现流式输出。

> Python < 3.11 的异步场景需手动传 `RunnableConfig` 给 `ainvoke()`，否则流式上下文无法正确传递。

```python
from dataclasses import dataclass
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START


@dataclass
class MyState:
    topic: str
    joke: str = ""


model = init_chat_model(model="gpt-4.1-mini")

def call_model(state: MyState):
    model_response = model.invoke(
        [
            {"role": "user", "content": f"Generate a joke about {state.topic}"}
        ]
    )
    return {"joke": model_response.content}

graph = (
    StateGraph(MyState)
    .add_node(call_model)
    .add_edge(START, "call_model")
    .compile()
)

for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode="messages",
    version="v2",
):
    if chunk["type"] == "messages":
        message_chunk, metadata = chunk["data"]
        if message_chunk.content:
            print(message_chunk.content, end="|", flush=True)
```

### 按 LLM 调用过滤

可以在模型初始化时加 `tags`，再依据 `metadata["tags"]` 过滤流。

### 按节点过滤

可以依据 `metadata["langgraph_node"]` 仅显示特定节点产出的 token。

## 自定义数据流

在节点或工具中发送自定义流事件：

1. 通过 `get_stream_writer()` 获取 writer 并写入数据。
2. 调用 `.stream()` / `.astream()` 时设置 `stream_mode="custom"`（可与其他 mode 组合，但必须包含 `custom`）。

```python
from typing import TypedDict
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START

class State(TypedDict):
    query: str
    answer: str

def node(state: State):
    writer = get_stream_writer()
    writer({"custom_key": "Generating custom data inside node"})
    return {"answer": "some data"}

graph = (
    StateGraph(State)
    .add_node(node)
    .add_edge(START, "node")
    .compile()
)

for chunk in graph.stream({"query": "example"}, stream_mode="custom", version="v2"):
    if chunk["type"] == "custom":
        print(f"Custom event: {chunk['data']['custom_key']}")
```

> Python < 3.11 的异步代码中，`get_stream_writer()` 不可用；需改为在函数签名中显式接收 `writer` 参数。

## 子图输出流

在父图 `stream()` 时设置 `subgraphs=True`，可同时接收父图与子图事件。

在 v2 中，仍使用统一 `StreamPart`，通过 `chunk["ns"]` 判断来源：
- 根图通常是 `()`
- 子图是形如 `("node_name:<task_id>",)` 的命名空间

```python
for chunk in graph.stream(
    {"foo": "foo"},
    subgraphs=True,
    stream_mode="updates",
    version="v2",
):
    print(chunk["type"])
    print(chunk["ns"])
    print(chunk["data"])
```

## Checkpoints

`checkpoints` mode 可在图执行中接收检查点事件，格式与 `get_state()` 一致。需要配置 checkpointer。

```python
from langgraph.checkpoint.memory import MemorySaver

graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node(generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .add_edge("generate_joke", END)
    .compile(checkpointer=MemorySaver())
)

config = {"configurable": {"thread_id": "1"}}

for chunk in graph.stream(
    {"topic": "ice cream"},
    config=config,
    stream_mode="checkpoints",
    version="v2",
):
    if chunk["type"] == "checkpoints":
        print(chunk["data"])
```

## Tasks

`tasks` mode 可接收任务开始/结束事件、结果与错误信息。需要 checkpointer。

## Debug

`debug` mode 会尽可能输出完整执行信息，包含节点名与状态，并结合 `checkpoints`、`tasks` 以及额外元数据。

## 同时使用多个 mode

可将 `stream_mode` 设为列表，例如：

```python
for chunk in graph.stream(inputs, stream_mode=["updates", "custom"], version="v2"):
    if chunk["type"] == "updates":
        for node_name, state in chunk["data"].items():
            print(f"Node `{node_name}` updated: {state}")
    elif chunk["type"] == "custom":
        print(f"Custom event: {chunk['data']}")
```

## 进阶

### 与任意 LLM 集成

即使某个 LLM API 不实现 LangChain chat model 接口，也可以在节点中调用其原生流接口，然后通过 `get_stream_writer()` 把片段写到 `custom` 流。

```python
from langgraph.config import get_stream_writer

def call_arbitrary_model(state):
    writer = get_stream_writer()
    for chunk in your_custom_streaming_client(state["topic"]):
        writer({"custom_llm_chunk": chunk})
    return {"result": "completed"}
```

### 为特定 chat model 禁用流式

若系统中混用支持和不支持流式的模型，可在初始化时关闭流式：
- `streaming=False`
- 某些模型可用 `disable_streaming=True`

```python
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-6",
    streaming=False,
)
```

## 迁移到 v2

v2 的核心变化：统一输出结构。

- 单 mode：v1 返回原始 dict，v2 返回 `StreamPart`
- 多 mode：v1 返回 `(mode, data)`，v2 仍返回 `StreamPart`
- 子图：v1 返回 `(namespace, data)`，v2 通过 `chunk["ns"]` 表达
- `invoke()`：v2 返回 `GraphOutput`（含 `.value`、`.interrupts`）

### v2 的 `invoke()` 返回格式

```python
from langgraph.types import GraphOutput

result = graph.invoke(inputs, version="v2")

assert isinstance(result, GraphOutput)
result.value
result.interrupts
```

> 对 `GraphOutput` 的字典式访问（如 `result["key"]`）仍兼容但已弃用，未来会移除。

### Pydantic 与 dataclass 状态类型收敛

当状态类型是 Pydantic 模型或 dataclass 时，v2 的 `values` 流会自动把输出收敛为对应类型实例。

## Python < 3.11 的异步注意事项

由于 Python < 3.11 的 `asyncio.create_task` 不支持 `context` 参数，LangGraph 的上下文自动传播受限，会带来两点影响：

1. 异步 LLM 调用必须显式把 `RunnableConfig` 传给 `ainvoke()`。
2. 异步节点/工具不能使用 `get_stream_writer()`，需要在函数参数中接收 `writer`。

示例（手动传 `config`）：

```python
async def call_model(state, config):
    joke_response = await model.ainvoke(
        [{"role": "user", "content": f"Write a joke about {state['topic']}"}],
        config,
    )
    return {"joke": joke_response.content}
```

示例（异步函数签名接收 `writer`）：

```python
from langgraph.types import StreamWriter

async def generate_joke(state: State, writer: StreamWriter):
    writer({"custom_key": "Streaming custom data while generating a joke"})
    return {"joke": f"This is a joke about {state['topic']}"}
```

## 参考链接

- Streaming 文档页：<https://docs.langchain.com/oss/python/langgraph/streaming>
- Stream API（Pregel）：<https://reference.langchain.com/python/langgraph/pregel/#langgraph.pregel.Pregel.stream>
- LangGraph 类型定义：<https://reference.langchain.com/python/langgraph/types/>
- `get_stream_writer`：<https://reference.langchain.com/python/langgraph/config/get_stream_writer>

