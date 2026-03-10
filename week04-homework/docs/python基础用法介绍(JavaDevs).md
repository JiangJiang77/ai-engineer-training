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
