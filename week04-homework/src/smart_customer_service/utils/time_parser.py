"""时间解析工具

将自然语言时间表达转换为具体日期
"""
from datetime import datetime, timedelta
import re


def parse_relative_time(text: str, reference_time: datetime = None) -> datetime:
    """解析相对时间表达
    
    Args:
        text: 时间表达文本,如"昨天"、"今天"、"前天"
        reference_time: 参考时间,默认为当前时间
    
    Returns:
        解析后的日期时间
    """
    if reference_time is None:
        reference_time = datetime.now()
    
    # 移除空格
    text = text.strip()
    
    # 今天
    if "今天" in text or "今日" in text:
        return reference_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 昨天
    if "昨天" in text or "昨日" in text:
        return (reference_time - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 前天
    if "前天" in text:
        return (reference_time - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 明天
    if "明天" in text or "明日" in text:
        return (reference_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # N天前
    match = re.search(r'(\d+)天前', text)
    if match:
        days = int(match.group(1))
        return (reference_time - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 本周/上周
    if "本周" in text:
        days_since_monday = reference_time.weekday()
        return (reference_time - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    if "上周" in text:
        days_since_monday = reference_time.weekday() + 7
        return (reference_time - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 默认返回今天
    return reference_time.replace(hour=0, minute=0, second=0, microsecond=0)


def extract_time_expressions(text: str) -> list:
    """从文本中提取时间表达式
    
    Args:
        text: 输入文本
    
    Returns:
        时间表达式列表
    """
    time_patterns = [
        r'昨天', r'今天', r'前天', r'明天',
        r'\d+天前', r'本周', r'上周'
    ]
    
    expressions = []
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        expressions.extend(matches)
    
    return expressions
