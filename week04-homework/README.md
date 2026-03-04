# 第四周作业

## 任务
构建一个小型多轮对话智能客服,支持工具调用以及模型与插件的热更新。

## 作业思路指导
### 阶段一:基础对话系统搭建
使用 LangChain 构建基础 Chain:Prompt → LLM → OutputParser
用户说"我昨天下的单",系统能结合当前时间推断"昨天"的具体日期

### 阶段二:多轮对话与工具调用
实现"订单查询""退款申请"等多轮交互流程,支持工具自动调用。
使用 LangGraph 构建以下流程:
- 用户说"查订单" → 追问"请提供订单号"
- 收到订单号后 → 调用 query_order(order_id) 工具
- 返回订单状态与物流信息

### 阶段三:热更新与生产部署
实现模型与插件的热更新,完成系统部署与监控。
1. 模型热更新
2. 插件热重载
3. 暴露健康检查接口 /health
4. 编写自动化测试脚本
- 测试"发票开具"插件的功能正确性
- 验证热更新后旧会话不受影响

## 如何提交作业
请fork本仓库,然后在以下目录分别完成编码作业:
- [week04-homework/smart_customer_service](./smart_customer_service)

其中:
- main.py是作业的入口


完成作业后,请在【极客时间】上提交你的fork仓库链接,精确到本周的目录,例如:
```
https://github.com/your-username/ai-engineer-training/tree/main/week04-homework
```

---

# 项目实现说明

## ✅ 已实现功能

### 核心模块

1. **配置管理** (`smart_customer_service/config/`)
   - 环境变量加载与管理
   - 数据库配置
   - ReAct Agent配置
   - 阿里云服务配置(预留)

2. **数据库模块** (`smart_customer_service/database/`)
   - SQLite数据库(零配置,单文件存储)
   - SQLAlchemy ORM模型定义
   - 用户认证(bcrypt密码加密)
   - 对话记录持久化
   - 订单CRUD操作

3. **ReAct Agent模块** (`smart_customer_service/agents/`) 🌟
   - `CustomerServiceReActAgent`: 具备推理能力的智能Agent
   - 5个核心工具:
     - `query_orders_tool`: 查询订单
     - `get_logistics_tool`: 获取物流信息
     - `submit_refund_tool`: 提交退款申请
     - `issue_invoice_tool`: 开具发票
     - `search_policy_tool`: RAG政策检索
   - 动态推理和工具选择
   - 多步推理支持
   - 自然语言理解

4. **RAG检索模块** (`smart_customer_service/rag/`)
   - 文档加载器(支持Markdown)
   - 向量存储(ChromaDB)
   - 相似度搜索
   - 政策文档检索

5. **LangGraph工作流** (`smart_customer_service/workflow/`)
   - 意图识别节点
   - 上下文管理节点
   - 物流查询节点
   - 退款处理节点
   - 发票开具节点
   - 政策检索节点(RAG)
   - LLM对话节点

6. **订单工具** (`smart_customer_service/tools/order_tools.py`)
   - `query_order_by_keyword`: 根据关键字和日期查询订单
   - `query_orders_by_date`: 根据日期查询订单列表
   - `get_order_logistics`: 获取订单物流状态
   - `query_refundable_orders`: 查询可退款订单
   - `submit_refund`: 提交退款申请
   - `query_invoiceable_orders`: 查询可开票订单
   - `issue_invoice`: 开具发票

7. **工具模块** (`smart_customer_service/utils/`)
   - 时间解析工具(支持"昨天"、"今天"等自然语言)
   - 日志工具

## 🛠️ 技术栈

| 组件 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| 数据库 | SQLite | 3.x | 零配置,单文件存储 |
| ORM | SQLAlchemy | >=2.0.0 | 数据库操作 |
| 密码加密 | bcrypt | >=4.0.0 | 用户密码哈希 |
| 工具框架 | LangChain | >=0.3.0 | 工具定义和调用 |
| 工作流引擎 | LangGraph | >=0.2.6 | 多轮对话流程(待实现) |
| LLM | 通义千问 | qwen-turbo | 意图识别(待集成) |
| 前端框架 | Gradio | >=4.0 | 交互界面(待实现) |

## 📁 项目结构

```
week04-homework/
├── smart_customer_service/      # 主程序包
│   ├── config/                  # 配置管理
│   │   └── settings.py
│   ├── database/                # 数据库模块
│   │   ├── models.py            # ORM模型
│   │   ├── crud.py              # CRUD操作
│   │   └── init_db.py           # 初始化脚本
│   ├── agents/                  # ReAct Agent模块 🌟
│   │   ├── __init__.py
│   │   ├── tools.py             # 工具定义
│   │   ├── prompts.py           # Prompt模板
│   │   └── react_agent.py       # Agent实现
│   ├── rag/                     # RAG检索模块
│   │   ├── document_loader.py   # 文档加载
│   │   └── vector_store.py      # 向量存储
│   ├── workflow/                # LangGraph工作流
│   │   ├── state.py             # 状态定义
│   │   ├── nodes.py             # 节点实现
│   │   ├── edges.py             # 边逻辑
│   │   └── graph.py             # 图构建
│   ├── tools/                   # 工具模块
│   │   ├── order_tools.py       # 订单工具
│   │   └── multimodal_tools.py  # 多模态(预留)
│   ├── utils/                   # 工具函数
│   │   ├── time_parser.py       # 时间解析
│   │   └── logger.py            # 日志
│   └── main.py                  # 主程序
├── data/                        # 数据目录
│   ├── customer_service.db      # SQLite数据库
│   └── chroma_db/               # 向量数据库
├── policy.md                    # 政策文档
├── qa.md                        # QA文档
├── pyproject.toml               # 项目配置
├── .env.example                 # 环境变量示例
└── README.md                    # 本文件
```


## 🚀 快速开始

### 1. 安装依赖

```bash
cd week04-homework
uv sync
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件,填入DASHSCOPE_API_KEY等配置
```

### 3. 初始化数据库

```bash
.venv/bin/python -m smart_customer_service.repository.db --load-mock-data
```

输出示例:
```
✅ 数据库表创建成功
✅ 创建测试用户: test_user
✅ 创建订单: 年货礼品大礼包
✅ 创建订单: 智能手表
✅ 创建订单: 笔记本电脑
✅ 创建订单: 无线耳机
```

### 4. 运行演示程序

> [!NOTE]
> 系统现在支持两种运行模式:
> - **ReAct Agent模式**(推荐): 具备推理能力,可动态选择工具
> - **Workflow模式**: 原有基于规则的工作流

#### 方式1: ReAct Agent模式(推荐 🌟)

```bash
# 演示模式 - 运行3个测试用例
.venv/bin/python -m smart_customer_service.demo --mode react

# 交互模式 - 与ReAct Agent实时对话
.venv/bin/python -m smart_customer_service.demo --mode react --interactive
```

**ReAct Agent特点**:
- ✅ 动态推理并选择合适的工具
- ✅ 支持多步推理场景
- ✅ 理解模糊的自然语言表达
- ✅ 集成RAG政策检索
- ✅ 主动询问缺失信息

**测试用例**:
1. "查询我昨天买的笔记本电脑" - 订单查询
2. "我想退掉那个贵的订单" - 复杂推理
3. "你们的退货政策是什么?" - RAG政策检索

#### 方式2: LangGraph工作流模式

```bash
# 演示模式 - 运行6个测试场景
.venv/bin/python -m smart_customer_service.main --mode workflow

# 交互模式 - 基于规则的对话
.venv/bin/python -m smart_customer_service.main --mode workflow --interactive
```

这将运行6个测试场景:
1. 物流查询 - 关键字场景
2. 物流查询 - 日期场景  
3. 退款申请
4. 发票开具
5. 一般对话
6. 未知意图

#### 方式3: 原始工具演示


```bash
# 查看原始工具调用演示
.venv/bin/python -c "
from smart_customer_service.database import get_user_by_username
from smart_customer_service.tools import query_order_by_keyword

user = get_user_by_username('test_user')
result = query_order_by_keyword.invoke({
    'user_id': user['user_id'],
    'keyword': '年货',
    'date_str': '昨天'
})
print(result)
"
```

### 5. 运行测试用例

```bash
# 运行所有测试
.venv/bin/python -m unittest tests.test_customer_service -v

# 运行特定测试类
.venv/bin/python -m unittest tests.test_customer_service.TestDatabaseOperations -v
```

测试结果示例:
```
Ran 16 tests in 0.862s
OK
```

## 🧪 测试数据

- **测试用户**: `test_user` (密码: `password123`)
- **模拟订单**: 4个订单(年货礼品、智能手表、笔记本电脑、无线耳机)

## 📋 功能演示

运行主程序会自动演示:
1. 订单查询(关键字、日期)
2. 可退款订单查询
3. 可开票订单查询

## 🧪 测试用例

项目包含完整的测试套件,共16个测试用例:

### 测试覆盖

1. **数据库操作测试** (6个用例)
   - 用户认证
   - 订单查询(全部/日期/关键字/可退款/可开票)

2. **订单工具测试** (4个用例)
   - 关键字查询工具
   - 日期查询工具
   - 可退款订单查询工具
   - 可开票订单查询工具

3. **时间解析测试** (4个用例)
   - 解析"昨天"、"今天"、"前天"
   - 解析"N天前"

4. **集成测试** (2个用例)
   - 完整订单查询流程
   - 完整退款流程

### 运行测试

```bash
# 运行所有测试
.venv/bin/python -m unittest tests.test_customer_service -v

# 查看测试文档
cat tests/README.md
```

详细测试文档请查看: [tests/README.md](./tests/README.md)

## 🔄 下一步开发

- [ ] LangGraph工作流(意图识别、工具调用、对话生成)
- [ ] Gradio界面(登录、聊天、会话管理)
- [ ] 通义千问LLM集成
- [ ] 多模态功能(ASR/OCR)
- [ ] 热更新机制

## 📚 相关文档

- [实现计划](./实现计划.md) - 详细技术设计
- [产品需求文档](./产品需求文档_智能客服系统.md) - 完整需求

## 🐛 常见问题

**Q: 如何重置数据库?**  
A: `rm -f data/customer_service.db && .venv/bin/python -m smart_customer_service.database.init_db --load-mock-data`

**Q: 订单查询返回空?**  
A: 确保运行了数据库初始化脚本并使用`--load-mock-data`参数

## 💡 技术亮点

1. **ReAct Agent架构**: 基于LangGraph实现具备推理能力的智能Agent
2. **RAG政策检索**: 使用ChromaDB向量数据库实现语义检索
3. **双模式支持**: ReAct Agent + Workflow,灵活切换
4. **Session管理**: CRUD函数返回字典,避免SQLAlchemy DetachedInstanceError
5. **时间解析**: 支持"昨天"、"今天"等自然语言
6. **工具框架**: 使用LangChain `@tool`装饰器
7. **密码安全**: bcrypt哈希,不存储明文
8. **模块化设计**: 清晰的目录结构




📋 下一步工作
LangGraph工作流集成
Gradio用户界面
通义千问LLM集成
阿里云ASR/OCR集成
热更新机制