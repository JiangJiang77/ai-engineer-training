# MCP 知识总结

## 1. MCP 是什么

MCP 全称是 `Model Context Protocol`，可以理解为一种让大模型或 Agent 以统一方式调用外部能力的协议。

它的目标不是替代 HTTP API，而是为模型提供一层标准化的“工具接入协议”，让不同客户端和不同服务端之间可以稳定协作。

常见理解方式：

- `HTTP API` 面向前端、后端、第三方系统
- `MCP` 面向 LLM、Agent、IDE、智能助手

简单说，MCP 解决的是“模型如何发现并调用工具”的标准化问题。

## 2. MCP 的核心组成

一个 MCP Server 通常会暴露以下几类能力：

- `Tools`：可执行动作，比如查询天气、调用内部系统、执行检索
- `Resources`：可读取上下文，比如文档、配置、数据源
- `Prompts`：可复用的提示模板

在使用关系上，通常是：

1. MCP Client 连接 MCP Server
2. Client 获取可用的 tools/resources/prompts
3. 模型根据任务选择合适的工具
4. 工具执行结果再回到模型上下文中

## 3. MCP 和普通 API 的区别

两者不是互斥关系，很多时候是叠加关系。

普通 API 的特点：

- 面向程序员或系统集成
- 调用方式由业务代码决定
- 重点是接口契约、鉴权、服务治理

MCP 的特点：

- 面向大模型工具调用
- 重点是工具发现、参数 schema、上下文协作
- 更适合接入 Agent、IDE、AI 工作流

一句话总结：

- `API` 是系统对系统
- `MCP` 是模型对工具

## 4. Python 里常见的三种写法

下面三种导入方式经常会被放在一起比较，但它们不是同一层面的抽象。

### 4.1 `from mcp.server.fastmcp import FastMCP`

这是官方 MCP Python SDK 的高层入口，适合直接编写一个原生 MCP Server。

它的特点是：

- `MCP-first`
- 不要求你先有 FastAPI 项目
- 直接用 Python 函数定义 tool/resource/prompt
- 更适合新建 MCP 服务

示例：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    return a + b
```

适用场景：

- 从 0 开始写 MCP Server
- 需要精细控制 MCP 工具定义
- 不想先维护一套 REST API 再映射

### 4.2 `from mcp.server.fastapi import FastApiServer`

这个名字容易和 `FastMCP`、`FastApiMCP` 混淆。

截至 `2026-03-13`，当前官方 `mcp` Python SDK 中并不是标准推荐入口；在本地核对的 `mcp==1.26.0` 环境里，也没有 `mcp.server.fastapi` 这个模块。

因此在实际判断上，应优先把它视为以下几种情况之一：

- 旧版本示例
- 过时写法
- 私有封装
- 与其他库名混淆

结论：

- 新项目不要把 `FastApiServer` 当成官方主路线
- 如果在旧代码里看到它，需要先确认它来自哪个库、哪个版本

### 4.3 `from fastapi_mcp import FastApiMCP`

这是第三方库 `FastAPI-MCP` 的入口，不属于官方 MCP Python SDK。

它的定位非常清楚：

- `FastAPI-first`
- 把已有的 FastAPI endpoints 自动暴露成 MCP tools
- 复用现有路由、Pydantic schema、依赖注入和鉴权逻辑

示例：

```python
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI()

mcp = FastApiMCP(app)
mcp.mount_http()
```

适用场景：

- 已经有现成的 FastAPI 服务
- 希望尽快让 Agent 使用已有 API
- 希望少写协议适配代码

## 5. 三者的本质区别

最核心的差别，不是“语法不同”，而是“起点不同”。

### 5.1 `FastMCP`

起点是 MCP 本身。

你直接定义：

- 哪些工具给模型使用
- 每个工具的输入输出是什么
- 服务以什么 MCP 形式暴露

这属于“原生 MCP Server 开发”。

### 5.2 `FastApiMCP`

起点是已有 FastAPI 应用。

你不是重新设计工具，而是把已有 API 转换成模型能调用的工具层。

这属于“FastAPI 到 MCP 的适配层”。

### 5.3 `FastApiServer`

它不是当前官方主流方案的稳定入口，至少不能默认这样理解。

如果项目里出现它，优先做版本核对，不要直接照抄到新项目里。

## 6. 该怎么选

### 选 `FastMCP` 的情况

- 你要做一个真正的 MCP 原生服务
- 工具设计是围绕模型调用来做的
- 不需要先有 REST API

### 选 `FastApiMCP` 的情况

- 你已经有 FastAPI 项目
- 目标是快速把已有 API 暴露给 Agent
- 想保留既有的 schema、依赖注入、鉴权逻辑

### 不建议默认选 `FastApiServer` 的情况

- 新项目
- 需要跟随官方 SDK 当前主线
- 没有确认该导入来源时

## 7. 一句话判断

如果你在做“面向模型设计工具”，优先考虑 `FastMCP`。

如果你在做“把已有 FastAPI 能力开放给模型”，优先考虑 `FastApiMCP`。

如果你看到 `FastApiServer`，先核实版本和来源，再决定是否保留。

## 8. 推荐实践

在工程实践里，通常建议按下面思路判断：

1. 如果项目还没开始，优先判断是不是应该直接做 `FastMCP`
2. 如果业务接口已经稳定，优先考虑 `FastApiMCP`
3. 如果代码里出现 `FastApiServer`，先做兼容性核对，不要默认它是现行标准

## 9. 当前结论

基于当前整理，可以把这三者概括为：

- `FastMCP`：官方 SDK，高层原生 MCP Server 开发入口
- `FastApiMCP`：第三方库，把 FastAPI 自动暴露为 MCP 工具
- `FastApiServer`：当前不应默认视为官方推荐主入口，需先核对来源和版本

这也是在 Python 生态里最容易混淆、但最需要先分清的一组概念。
