# 代码练习需求：长期记忆系统 (LangGraph + Redis)

## 1. 案例背景
设计一个具备长期记忆能力的聊天系统。与默认的短期记忆（MemorySaver）不同，该系统需要将对话历史保存到外部数据库（如 Redis），从而实现：
- **跨会话持久化**：即使程序重启，之前的聊天记录依然存在。
- **多用户隔离**：根据 `thread_id` 区分不同用户的记忆，互不干扰。
- **可控管理**：支持手动查询和清除特定用户的记忆。

## 2. 状态定义 (State)
定义 `GraphState` 状态类：
- `messages`: 使用 `Annotated[Sequence, add_messages]`，用于在图中流转对话历史。

## 3. 长期记忆管理类 (LongTermMemory)
实现一个管理类，直接操作 Redis 存储：
- **存储逻辑**：将消息序列化为 JSON 格式（包含类型：`human/ai` 和内容：`content`），使用 Redis 的列表（List）结构存储。
- **核心方法**：
    - `save_memory(memory_type, content)`：向 Redis 列表中插入一条新记录。
    - `get_memory(limit)`：从 Redis 中读取最近的 N 条记录，并反序列化回 `HumanMessage` 或 `AIMessage` 对象列表。
    - `clear_memory()`：删除 Redis 中对应的键。

## 4. 节点功能 (Nodes)
实现核心聊天节点 `chat_node`：
1. **保存现场**：将当前收到的用户消息（`state["messages"][-1]`）及时存入 Redis。
2. **加载历史**：从 Redis 中提取该用户之前的对话历史。
3. **构建上下文**：将“历史记录 + 当前消息”组合，作为 LLM 的输入。
4. **生成并存记录**：调用大模型生成回复，并将 AI 的回复也存入 Redis。
5. **返回更新**：将 AI 回复返回给图中。

## 5. 流程拓扑 (Workflow)
- 简单的线性流程：`START` -> `chat_node` -> `END`。
- 编译时可以配合 `MemorySaver` 作为短期 Checkpointer，但业务逻辑主要依赖 `LongTermMemory`。

## 6. 验证场景 (Testing)
编写测试脚本模拟以下行为：
- **Alice 环节**：
    1. 用户 Alice 说：“我是 Alice，我喜欢读书”。
    2. 用户 Alice 问：“我刚才说喜欢什么？”。
    *预期：AI 能够准确回答出她喜欢读书。*
- **Bob 环节**：
    1. 用户 Bob 说：“我是 Bob，我喜欢运动”。
    2. 用户 Bob 问：“我叫什么名字？”。
    *预期：AI 记得他叫 Bob，且不会混淆 Alice 的信息。*
- **管理环节**：
    1. 打印查看 Alice 和 Bob 的 Redis 记录。
    2. 清除 Alice 的记忆，再次查询应为空。
