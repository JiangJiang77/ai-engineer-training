from src.context import select_relevant


def test_select_relevant():
    messages = [
        {"role": "user", "content": "We need a retry policy for API calls"},
        {"role": "assistant", "content": "Sure, exponential backoff works"},
        {"role": "user", "content": "Also add logging for failures"},
        {"role": "assistant", "content": "Logging added in the handler"},
    ]
    out = select_relevant(messages, query="retry policy logging", max_items=2)
    assert out == [
        {"role": "user", "content": "We need a retry policy for API calls"},
        {"role": "user", "content": "Also add logging for failures"},
    ]
