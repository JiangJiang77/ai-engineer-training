# MCP 知识总结

## 1. FastAPI 挂载到 MCP 的最佳实践

### 1.1 最小可用结构

FastAPI 挂载到 MCP 的核心步骤只有 4 步：

1. 定义 FastAPI 应用和路由
2. 用 `FastApiMCP` 包装 FastAPI 应用
3. 调用 `mount()` 或 `mount_http()` / `mount_sse()` 挂载 MCP 路由
4. 启动时运行已经挂载 MCP 的应用实例

参考当前示例 [p23-mcp-fastapi.py](/Users/culiang/Documents/GitHub/ai-engineer-training/week05-homework/demos/p23-mcp-fastapi.py)：

```python
api_app = create_api_app()
api_mcp_app = create_api_mcp_app(api_app)
uvicorn.run(api_mcp_app, host="0.0.0.0", port=8001)
```

### 1.2 推荐写法

#### 路由层

每个 API 最好显式补齐以下信息：

- `operation_id`
- `description`
- 函数 `docstring`
- 明确的参数类型标注

示例：

```python
@api_app.get(
    "/weather",
    operation_id="get_weather",
    description="根据城市名称返回天气描述。当前示例支持北京和上海，其他城市返回未知城市。",
)
def get_weather(city: str):
    """查询指定城市的天气信息。"""
```

这样做的好处：

- OpenAPI 中的接口标识稳定，不依赖 FastAPI 自动生成
- MCP 暴露出来的 tool 名更清晰
- AI 客户端更容易理解 tool 的用途和参数
- 后续排查 `tools/list`、`tools/call` 时更直观

#### MCP Server 层

建议在 `FastApiMCP(...)` 中至少配置：

- `name`
- `description`，可选但建议加
- `describe_all_responses=True`
- `describe_full_response_schema=True`

示例：

```python
fast_api_mcp = FastApiMCP(
    api_app,
    name="My API MCP",
    description="将天气查询和穿衣建议接口暴露为 MCP tools",
    describe_all_responses=True,
    describe_full_response_schema=True,
)
```

说明：

- `name` 用于标识整个 MCP Server
- `description` 不是强制项，但建议提供，便于客户端或代理理解 Server 能力
- `describe_all_responses` 和 `describe_full_response_schema` 可以让工具描述更完整，利于模型理解返回结构

### 1.3 operation_id 的作用

`operation_id` 是 OpenAPI 中接口的唯一标识。API 挂载到 MCP 后，它通常会被直接用作 tool name，或者作为 tool name 的生成基础。

例如在当前示例中：

- `/weather` 对应 `operation_id="get_weather"`
- `/cloth_recommendation` 对应 `operation_id="get_cloth_recommendation"`

所以在 MCP 中通常会看到对应工具名：

- `get_weather`
- `get_cloth_recommendation`

最佳实践：

- 不要依赖 FastAPI 自动生成的 `operationId`
- 手动设置 `operation_id`
- 命名尽量用动作 + 语义对象，例如 `get_weather`、`get_cloth_recommendation`

### 1.4 常见错误

#### 错误 1：启动了错误的 app

如果代码里先做了：

```python
api_mcp_app = create_api_mcp_app(api_app)
```

但最后启动的是：

```python
uvicorn.run(api_app, ...)
```

那么普通 REST API 可以访问，但 MCP 路由不会真正暴露出来。

这正是当前 [p23-mcp-fastapi.py](/Users/culiang/Documents/GitHub/ai-engineer-training/week05-homework/demos/p23-mcp-fastapi.py#L60) 里的问题。  
如果要让 `/mcp` 可用，应该启动挂载后的 `api_mcp_app`。

#### 错误 2：把 `operationId` 写成 FastAPI 不识别的参数名

FastAPI 路由装饰器参数应使用 `operation_id`，不是 `operationId`。

正确写法：

```python
@api_app.get("/weather", operation_id="get_weather")
```

#### 错误 3：缺少描述信息

虽然缺少 `description` 或 docstring 不会阻止程序运行，但会让 MCP tool 的可读性变差，影响模型选工具和传参的准确性。

### 1.5 SSE 模式下的挂载结论

在本次对话中确认了 `fastapi-mcp 0.4.0` 的行为：

- `mount()` 默认挂载路径是 `/mcp`
- `mount()` 默认走的是 SSE 传输
- 实际注册出的路由通常是：
  - `GET /mcp`
  - `POST /mcp/messages/`

也就是说，MCP 并不是把每个 FastAPI 接口都暴露成新的 HTTP 路径，而是把这些接口统一封装为 MCP tools，通过同一条 MCP 会话来调用。

## 2. API 挂载到 MCP 后的调用链路说明

### 2.1 整体链路

FastAPI API 挂载到 MCP 后，调用链路不是：

`客户端 -> /weather`

而是：

`MCP 客户端 -> /mcp 建立会话 -> /mcp/messages/ 发送 JSON-RPC 请求 -> MCP tool -> FastAPI 路由函数 -> 返回结果通过 SSE 回传`

也就是说，MCP 调用是对 API 的二次封装。

### 2.2 对外暴露的接口

在 SSE 模式下，客户端主要只接触两个地址：

- `GET /mcp`
  作用：建立 SSE 长连接
- `POST /mcp/messages/?session_id=...`
  作用：向该 MCP 会话发送 JSON-RPC 消息

示例地址：

- `http://127.0.0.1:8001/mcp`
- `http://127.0.0.1:8001/mcp/messages/?session_id=<真实会话ID>`

### 2.3 建链过程

#### 第 1 步：连接 `/mcp`

客户端先请求：

```bash
curl -N http://127.0.0.1:8001/mcp
```

服务端会建立 SSE 长连接，并先返回一条 `endpoint` 事件，告诉客户端后续消息该发到哪里：

```text
event: endpoint
data: /mcp/messages/?session_id=<真实session_id>
```

这里的 `session_id` 由服务端动态生成，必须使用真实值。

#### 第 2 步：向 `/mcp/messages/` 发消息

客户端需要把 JSON-RPC 请求发到：

```text
POST /mcp/messages/?session_id=<真实session_id>
```

如果 `session_id` 不是服务端刚刚生成的真实值，或者格式非法，就会返回：

```json
{"detail": "Invalid session ID"}
```

### 2.4 初始化链路

一个完整 MCP 会话通常要先走这几个步骤：

1. `initialize`
2. `notifications/initialized`
3. `tools/list`
4. `tools/call`

说明：

- `initialize`：建立 MCP 会话能力协商
- `notifications/initialized`：通知服务端客户端初始化完成
- `tools/list`：获取 MCP server 暴露的工具列表
- `tools/call`：调用某个具体工具

### 2.5 API 是如何变成 MCP Tool 的

FastAPI 路由并不会保留为独立 MCP URL，而是会被转换成工具。

例如本次示例中的两个接口：

- `GET /weather`
- `GET /cloth_recommendation`

挂载到 MCP 之后，不是通过：

- `GET /mcp/weather`
- `GET /mcp/cloth_recommendation`

这种方式调用，而是通过：

- `tools/list` 查看工具
- `tools/call` 调用工具

工具名通常来自 `operation_id`。

当前推荐的工具名应该是：

- `get_weather`
- `get_cloth_recommendation`

### 2.6 参数映射

普通 API 查询参数会映射为 MCP `arguments`。

例如原始 HTTP 调用：

```http
GET /weather?city=北京
```

对应的 MCP 调用参数是：

```json
{
  "name": "get_weather",
  "arguments": {
    "city": "北京"
  }
}
```

另一个例子：

```http
GET /cloth_recommendation?temperature=25
```

对应的 MCP 调用参数：

```json
{
  "name": "get_cloth_recommendation",
  "arguments": {
    "temperature": 25
  }
}
```

### 2.7 返回结果如何传回客户端

`POST /mcp/messages/` 的 HTTP 响应通常只是：

- `202 Accepted`

真正的工具执行结果不会直接放在 POST 响应体里，而是继续从最开始建立的 `/mcp` SSE 长连接中推送回来。

因此调试时通常要分两个终端：

1. 一个终端持续监听 `/mcp`
2. 另一个终端向 `/mcp/messages/` 发 JSON-RPC 消息

### 2.8 推荐调试顺序

调试 API 挂载 MCP 是否正常，可以按以下顺序排查：

1. 先确认普通 REST API 可用
2. 再确认 `GET /mcp` 可建立 SSE 连接
3. 确认服务端返回 `endpoint` 事件和真实 `session_id`
4. 发送 `initialize`
5. 发送 `notifications/initialized`
6. 调用 `tools/list`
7. 最后执行 `tools/call`

### 2.9 一句话总结

FastAPI 挂载到 MCP 后：

- 对开发者来说，核心工作是把 API 元数据补齐并正确挂载
- 对客户端来说，访问入口不再是每个业务 API 路径，而是统一通过 `/mcp` 和 `/mcp/messages/`
- 对模型来说，最终感知到的是一组有名字、参数和描述的 tools，而不是原始 HTTP 路由

## 3. MCP Prompt 定义与 `Unknown prompt` 排查

### 3.1 典型报错与根因

在 LangGraph + MCP 客户端场景中，如果客户端代码调用：

```python
await load_mcp_prompt(mcp_client_session, "system_prompt")
```

但 MCP Server 没有暴露同名 prompt，就会出现类似错误：

- `Unknown prompt: system_prompt`

根因通常是：

1. 服务端只定义了 `@mcp_server.tool()`，没有定义 `@mcp_server.prompt()`
2. 服务端定义了 prompt，但名称不是 `system_prompt`
3. 客户端请求名称与服务端注册名称不一致

参考当前示例：

- 客户端请求名在 [p24_Langraph-MCPClient.py](/Users/culiang/Documents/GitHub/ai-engineer-training/week05-homework/demos/p24_Langraph-MCPClient.py:50)
- 服务端当前仅定义 tools，在 [p24_Langraph-MCPServer.py](/Users/culiang/Documents/GitHub/ai-engineer-training/week05-homework/demos/p24_Langraph-MCPServer.py)

### 3.2 服务端正确写法（FastMCP）

最关键原则：客户端 `load_mcp_prompt(..., "<name>")` 的 `<name>` 必须与服务端 prompt 名完全一致。

示例：

```python
from mcp.server.fastmcp import FastMCP

mcp_server = FastMCP("物流助手")

@mcp_server.prompt(name="system_prompt")
def system_prompt() -> str:
    return "你是一个物流客服助手，优先调用工具回答包裹、运费、时效问题。"
```

如果不写 `name=`，则通常使用函数名作为 prompt 名；这时函数名就应命名为 `system_prompt`，确保与客户端一致。

### 3.3 客户端建议的容错方式

客户端侧继续保留兜底逻辑是合理的：

1. 先尝试加载 MCP prompt
2. 加载失败时回退到本地默认 system prompt

另外建议在调试时先打印服务端暴露的 prompts：

```python
print(await mcp_client_session.list_prompts())
```

这样可快速确认服务端是否真的注册了 `system_prompt`。

### 3.4 官方文档链接

- MCP 规范（Prompts）：`https://modelcontextprotocol.io/specification/2025-06-18/server/prompts`
- MCP Python SDK（FastMCP README，含 `@mcp.prompt` 用法）：`https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md`
- LangChain MCP Adapters（`load_mcp_prompt` 实现）：`https://github.com/langchain-ai/langchain-mcp-adapters/blob/main/langchain_mcp_adapters/prompts.py`
