# Python 语法说明示例（面向 Java 开发人员）

本文用于快速对照 Java 与 Python 常见语法，帮助从 Java 平滑切换到 Python。

## 1. 变量与类型

Java:
```java
int age = 18;
String name = "Alice";
```

Python:
```python
age = 18
name = "Alice"
```

说明：
- Python 是动态类型语言，变量定义时不需要显式声明类型。

## 2. 条件判断

Java:
```java
if (age >= 18) {
    System.out.println("adult");
} else {
    System.out.println("minor");
}
```

Python:
```python
if age >= 18:
    print("adult")
else:
    print("minor")
```

说明：
- Python 使用缩进表示代码块，而不是 `{}`。

## 3. 循环

Java:
```java
for (int i = 0; i < 3; i++) {
    System.out.println(i);
}
```

Python:
```python
for i in range(3):
    print(i)
```

## 4. 函数

Java:
```java
public int add(int a, int b) {
    return a + b;
}
```

Python:
```python
def add(a: int, b: int) -> int:
    return a + b
```

说明：
- Python 支持类型注解，但默认不强制。

## 5. 类

Java:
```java
public class User {
    private String name;

    public User(String name) {
        this.name = name;
    }
}
```

Python:
```python
class User:
    def __init__(self, name: str):
        self.name = name
```

## 6. List 常用语法（重点）

Python:
```python
items = ["a", "b", "c"]

first = items[0]    # 第一个元素: "a"
last = items[-1]    # 最后一个元素: "c"
```

关键点：
- `list[-1]` 就是列表最后一个元素。
- `list[-2]` 是倒数第二个元素，以此类推。

结合项目示例：
```python
last_message = event["messages"][-1]
```

这行代码表示：取 `messages` 列表中的最新一条消息（最后一条）。

## 7. 异常处理

Java:
```java
try {
    // code
} catch (Exception e) {
    e.printStackTrace();
}
```

Python:
```python
try:
    # code
except Exception as e:
    print(e)
```

## 8. 常见 Java -> Python 思维转换

- Java 的 `null` 对应 Python 的 `None`。
- Java 的 `System.out.println` 对应 Python 的 `print`。
- Java 的 `List<Map<String, Object>>` 在 Python 常常是 `list[dict]`（或 `List[Dict[str, Any]]`）。
- Python 通过切片快速处理列表：`items[1:3]`、`items[:-1]`。

## 9. 小结

- 先适应 Python 的缩进和动态类型。
- 日常开发中，类型注解 + 规范命名可以显著提升可维护性。
- 记住：`list[-1]` 是最后一个元素，这是处理消息流、日志流时非常常用的写法。

## 10. 函数签名中的 `*`（仅限关键字参数）

Python 示例：
```python
def add_node(node, action=None, *, defer=False, metadata=None):
    ...
```

关键点：
- `*` 前面的参数可以按位置传参。
- `*` 后面的参数必须使用“参数名=值”的方式传参（keyword-only）。

示例：
```python
add_node("agent", fn, defer=True, metadata={"k": "v"})  # 正确
add_node("agent", fn, True, {"k": "v"})                 # 错误
```

## 11. 参数可空与不可空（`None`）

关键规则：
- 类型标注 `name: str` 表示期望“不可为 `None`”。
- 类型标注 `name: str | None`（或 `Optional[str]`）表示“可以为 `None`”。
- 仅写类型标注通常是静态约束；运行时是否拦截，要靠你手动校验或框架（如 Pydantic）。

函数示例：
```python
def f1(name: str):  # 期望非 None
    if name is None:
        raise ValueError("name 不能为 None")

def f2(name: str | None = None):  # 允许 None
    return name
```

FastAPI / Pydantic 常见写法：
```python
from pydantic import BaseModel

class Req(BaseModel):
    required_name: str             # 必填，且不可为 None
    optional_name: str | None = None  # 可空，可不传（默认 None）
```
