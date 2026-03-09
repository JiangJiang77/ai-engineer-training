# LangGraph 官方文档速查表

本文用于快速定位 LangGraph 常用官方文档，优先覆盖流式处理相关内容。

## 1. Streaming（流式输出）

- 官方说明页（包含 `stream_mode="values"` 的使用方式）  
  https://docs.langchain.com/oss/python/langgraph/streaming

适用场景：
- 按事件/阶段读取图执行过程。
- 在对话场景中逐步拿到节点输出，再提取最终 AI 回复。

## 2. Graphs API Reference（`stream` 方法所在）

- 官方 API 参考（Python）  
  https://reference.langchain.com/python/langgraph/graphs/

查阅重点：
- `CompiledStateGraph` 相关方法（包括 `stream`）。
- `stream` 的参数与返回事件结构。

## 3. 与本项目代码对应关系

项目片段：
```python
for event in current_app.stream(
    {"messages": messages},
    config=config,
    stream_mode="values"
):
    if "messages" in event:
        last_message = event["messages"][-1]
```

对应说明：
- `current_app` 通常是 `workflow.compile()` 之后得到的图应用对象。
- `stream_mode="values"` 表示按状态值/事件值流式返回结果。
- `event["messages"][-1]` 取 `messages` 列表最后一条消息（最新消息）。

## 4. 备注

- 如需确认某个参数的最新定义，以官方 API Reference 为准。
- 文档地址可能随版本演进调整，若失效可从 LangGraph 文档首页跳转到对应章节。

## 5. 如何定义 Node

- 在 `StateGraph` 中定义一个可执行 `node`，本质上就是提供一个可调用对象（函数/异步函数/Runnable），它接收当前 `state` 并返回 `dict` 形式的状态更新（如 `{"messages": [...]}`）。
