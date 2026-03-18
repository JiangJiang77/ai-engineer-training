# Python 基础用法介绍（面向 Java 开发者）

## 1. Demo 代码路径

本仓库可参考示例代码：

- `llm_demo/llm_demo.py`

该文件演示了：

- 函数定义与参数默认值
- `class` 类型对象（如 `ChatTongyi`）的实例化与调用
- 流式与非流式调用（`chain.stream(...)` / `chain.invoke(...)`）

## 2. Python class 常见语法

### 2.1 定义类与构造函数

```python
class User:
    def __init__(self, name: str):
        self.name = name
```

对应 Java：

- `class` 类似 Java `class`
- `__init__` 类似构造初始化逻辑（但对象创建由 `__new__` + `__init__` 完成）
- `self` 类似 Java 的 `this`，但需要显式写在方法参数里

### 2.2 方法类型

```python
class Demo:
    def inst(self):
        return "instance"

    @classmethod
    def cls(cls):
        return "class"

    @staticmethod
    def stat():
        return "static"
```

- `inst(self)`：实例方法（最常见）
- `@classmethod`：类方法，第一个参数是 `cls`
- `@staticmethod`：静态方法，无 `self/cls`

### 2.3 继承与重写

```python
class Base:
    def run(self):
        print("base")

class Child(Base):
    def run(self):
        super().run()
        print("child")
```

- 继承语法：`class Child(Base)`
- 调父类：`super()`

### 2.4 特殊方法（魔术方法）

- `__init__`：初始化
- `__str__`：字符串展示
- `__len__`：支持 `len(obj)`

这些属于 Python 约定接口，类似 Java 中实现某些接口后可被框架调用。

## 3. 函数/方法名以下划线开头的含义

### 3.1 `_name`（单下划线前缀）

表示“内部使用”的约定（非强制私有）。

```python
def _create_llm(...):
    ...
```

含义：这个函数主要给模块内部调用，外部可以调用但不建议。

### 3.2 `__name`（双下划线前缀）

触发名称改写（name mangling），用于减少子类覆盖冲突。

```python
class A:
    def __hidden(self):
        pass
```

### 3.3 `__name__`（前后双下划线）

Python 保留的特殊命名（魔术方法/属性），如：

- `__init__`
- `__name__`

业务代码不要随意自定义这类命名。

## 4. 结合本项目的建议

- 内部工具函数可保留 `_` 前缀（如 `_create_llm`）
- 对外演示入口函数建议不用 `_`（如 `demo_llm_chain_streaming`）
- 流式调用必须传入输入参数：

```python
for chunk in chain.stream({}):
    print(chunk.content, end="", flush=True)
```

如果 `PromptTemplate` 里有变量（如 `{user_input}`），则必须传入对应 key。

## 5. 圆括号 `()` 用于多行表达式续行

在 Python 里，最外层的 `()` 可以把一整个表达式包起来，让它安全地换行书写，不改变原有语义。

结合 `week05/p13_langgraph_mas.py` 示例：

```python
multi_agent_graph = (
    StateGraph(MessagesState)
    .add_node(flight_assistant)
    .add_node(hotel_assistant)
    .add_edge(START, "flight_assistant")
    .compile()
)
```

等价的一行写法：

```python
multi_agent_graph = StateGraph(MessagesState).add_node(flight_assistant).add_node(hotel_assistant).add_edge(START, "flight_assistant").compile()
```

关键点：

- 这里的 `()` 不是函数调用参数，也不是 tuple。
- 主要作用是“分组 + 多行续行”，避免每行末尾写 `\`。
- 在链式调用场景中可读性更好。

## 6. 二元结构与解包赋值

### 6.1 什么是二元结构

二元结构就是“恰好包含 2 个元素”的结构。最常见的是二元组（2-tuple）：

```python
pair = ("flight_assistant", {"messages": []})
```

### 6.2 什么是解包（unpack）

解包是把结构中的多个元素，按位置一次性赋给多个变量：

```python
a, b = pair
```

等价于：

```python
a = pair[0]
b = pair[1]
```

### 6.3 结合项目代码

在 `week05/p13_langgraph_mas.py` 中有一行：

```python
ns, update = update
```

含义是：右侧 `update` 必须是一个“有两个元素”的结构（通常是 tuple），然后拆成：

- `ns`：命名空间信息
- `update`：实际更新数据

如果右侧元素个数不是 2，会触发解包错误（`ValueError`）。
