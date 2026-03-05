"""LangChain 双链路示例

需求:
1. Chain1: LLM 结构化解析用户问题(item/brand/time_expression/intent)
2. 系统执行 time_parse + query_orders + logistics_stats
3. Chain2: 基于工具结果生成自然语言回答
"""

from __future__ import annotations

from datetime import datetime, timedelta
import json
import re
from typing import Literal

from langchain_community.llms import Tongyi
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    """LLM 结构化解析结果"""

    item: str = Field(description="商品品类, 例如 手表")
    brand: str = Field(default="", description="品牌, 没有就返回空字符串")
    time_expression: str = Field(description="原始时间表达, 例如 昨天 / 上周一")
    intent: Literal["订单查询", "物流统计"] = Field(description="用户意图")


ORDERS = [
    {
        "order_id": "O20260301001",
        "item": "手表",
        "brand": "Apple",
        "order_date": "2026-03-04",
        "logistics_status": "运输中",
    },
    {
        "order_id": "O20260301002",
        "item": "手表",
        "brand": "华为",
        "order_date": "2026-03-03",
        "logistics_status": "已签收",
    },
    {
        "order_id": "O20260301003",
        "item": "耳机",
        "brand": "Sony",
        "order_date": "2026-03-04",
        "logistics_status": "揽收中",
    },
    {
        "order_id": "O20260301004",
        "item": "手表",
        "brand": "Casio",
        "order_date": "2026-02-23",
        "logistics_status": "派送中",
    },
]


WEEKDAY_MAP = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}


def time_parse(time_expression: str, reference_time: datetime) -> str:
    """解析中文时间表达为 yyyy-mm-dd"""

    expr = time_expression.strip()
    today = reference_time.replace(hour=0, minute=0, second=0, microsecond=0)

    if not expr:
        return today.strftime("%Y-%m-%d")
    if expr in {"今天", "今日"}:
        return today.strftime("%Y-%m-%d")
    if expr in {"昨天", "昨日"}:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    if expr == "前天":
        return (today - timedelta(days=2)).strftime("%Y-%m-%d")

    # 上周一/上周二...
    match = re.fullmatch(r"上周([一二三四五六日天])", expr)
    if match:
        target_weekday = WEEKDAY_MAP[match.group(1)]
        this_monday = today - timedelta(days=today.weekday())
        target_day = this_monday - timedelta(days=7) + timedelta(days=target_weekday)
        return target_day.strftime("%Y-%m-%d")

    # 本周一/本周二...
    match = re.fullmatch(r"本周([一二三四五六日天])", expr)
    if match:
        target_weekday = WEEKDAY_MAP[match.group(1)]
        this_monday = today - timedelta(days=today.weekday())
        target_day = this_monday + timedelta(days=target_weekday)
        return target_day.strftime("%Y-%m-%d")

    # 兼容直接给出日期
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", expr):
        return expr

    return today.strftime("%Y-%m-%d")


def query_orders(item: str, brand: str, parsed_date: str) -> list[dict]:
    """简易订单查询工具: 固定列表筛选"""

    result = []
    for order in ORDERS:
        item_ok = (not item) or (item in order["item"])
        brand_ok = (not brand) or (brand.lower() in order["brand"].lower())
        date_ok = parsed_date == order["order_date"]
        if item_ok and brand_ok and date_ok:
            result.append(order)
    return result


def logistics_stats(orders: list[dict]) -> dict:
    """物流统计工具: 聚合当前物流状态"""

    stats: dict[str, int] = {}
    for order in orders:
        status = order["logistics_status"]
        stats[status] = stats.get(status, 0) + 1
    return stats


def build_chain():
    parser = JsonOutputParser(pydantic_object=ParsedQuery)
    llm = Tongyi(temperature=0)
    prompt = PromptTemplate(
        template=(
            "你是订单意图解析器。\n"
            "请基于用户输入提取并只输出 JSON。\n"
            "规则:\n"
            "1) item 输出品类(如手表)\n"
            "2) brand 没提及就输出空字符串\n"
            "3) time_expression 提取原始时间词(如昨天、上周一)\n"
            "4) intent 只能是: 订单查询 或 物流统计\n"
            "{format_instructions}\n\n"
            "用户输入: {user_input}"
        ),
        input_variables=["user_input"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    return prompt | llm | parser


def build_reply_chain():
    llm = Tongyi(temperature=0.2)
    prompt = PromptTemplate(
        template=(
            "你是电商客服助手，请根据结构化信息与工具结果，用自然语言简洁回复用户。\n"
            "要求:\n"
            "1) 明确说明时间表达对应的具体日期\n"
            "2) 若有订单，列出订单号、商品、品牌、下单日期、物流状态\n"
            "3) 若无订单，明确告知未查询到符合条件的订单，并提示可补充品牌或日期\n"
            "4) 语气专业、简短，不要输出 JSON\n\n"
            "用户原话: {user_input}\n"
            "结构化解析结果: {parsed_query_json}\n"
            "时间解析结果: {time_parse_json}\n"
            "订单查询结果: {orders_json}\n"
            "物流统计结果: {stats_json}\n"
        ),
        input_variables=[
            "user_input",
            "parsed_query_json",
            "time_parse_json",
            "orders_json",
            "stats_json",
        ],
    )
    return prompt | llm | StrOutputParser()


def run_demo(user_input: str):
    parse_chain = build_chain()
    reply_chain = build_reply_chain()
    reference_time = datetime.now()

    # Chain1: 结构化解析
    parsed = parse_chain.invoke({"user_input": user_input})
    parsed_query = ParsedQuery(**parsed)

    # 工具调用
    parsed_date = time_parse(parsed_query.time_expression, reference_time)
    matched_orders = query_orders(parsed_query.item, parsed_query.brand, parsed_date)
    stats = logistics_stats(matched_orders)

    # Chain2: 生成自然语言回复
    final_reply = reply_chain.invoke(
        {
            "user_input": user_input,
            "parsed_query_json": json.dumps(parsed_query.model_dump(), ensure_ascii=False),
            "time_parse_json": json.dumps(
                {"time_expression": parsed_query.time_expression, "date": parsed_date},
                ensure_ascii=False,
            ),
            "orders_json": json.dumps(matched_orders, ensure_ascii=False),
            "stats_json": json.dumps(stats, ensure_ascii=False),
        }
    )

    result = {
        "now": reference_time.strftime("%Y-%m-%d %H:%M:%S"),
        "user_input": user_input,
        "llm_parsed": parsed_query.model_dump(),
        "time_parse_result": {"time_expression": parsed_query.time_expression, "date": parsed_date},
        "intent_result": {
            "intent": parsed_query.intent,
            "matched_orders": matched_orders,
            "logistics_stats": stats,
        },
        "final_reply": final_reply,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # 示例: 用户说“我昨天下单的手表”
    run_demo("我昨天下单的手表发货了吗")
