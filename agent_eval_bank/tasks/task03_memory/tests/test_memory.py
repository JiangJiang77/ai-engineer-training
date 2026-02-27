from src.memory import compact_history


def test_no_compaction_needed():
    msgs = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]
    out = compact_history(msgs, max_chars=100)
    assert out == msgs


def test_compaction():
    msgs = [
        {"role": "user", "content": "Book me a flight"},
        {"role": "assistant", "content": "From where?"},
        {"role": "user", "content": "SFO to JFK"},
        {"role": "assistant", "content": "What dates?"},
    ]
    out = compact_history(msgs, max_chars=30)
    assert out == [
        {"role": "system", "content": "Summary: Book me a flight | From where?"},
        {"role": "user", "content": "SFO to JFK"},
        {"role": "assistant", "content": "What dates?"},
    ]
