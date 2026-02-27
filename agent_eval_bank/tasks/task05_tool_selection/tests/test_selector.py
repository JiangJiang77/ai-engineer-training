from src.selector import choose_tool


TOOLS = [
    {"name": "web_search", "keywords": ["search", "web", "browse"]},
    {"name": "file_read", "keywords": ["file", "read", "open"]},
    {"name": "math_calc", "keywords": ["calculate", "math", "sum"]},
]


def test_choose_tool():
    assert choose_tool("Please search the web for this", TOOLS) == "web_search"
    assert choose_tool("Open the file and read lines", TOOLS) == "file_read"
    assert choose_tool("Calculate the sum", TOOLS) == "math_calc"


def test_no_match():
    assert choose_tool("Tell me a joke", TOOLS) is None
