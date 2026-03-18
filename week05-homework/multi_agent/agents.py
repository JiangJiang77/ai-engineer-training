import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage,AIMessage

from multi_agent.llm import llm_client
from multi_agent.tools.search_tool import search_tool
from multi_agent.prompts import PROMPTS

research_min_length = 300
draft_min_length = 150
fallback_score = 0.75
final_article_min_length = 200

def research_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    topic = state["topic"]
    sources = search_tool(topic)
    system_prompt = PROMPTS["research"]
    user_prompt = (
        f"主题：{topic}\n\n"
        f"搜索结果：{sources}\n\n"
        f"请基于以上结果输出研究报告,不少于 {research_min_length} 字。"
    )
    # report = llm_client.generate(
    #     prompt=[
    #         SystemMessage(content=system_prompt),
    #         HumanMessage(content=user_prompt),
    #     ]
    # )

    key_points = [item["summary"] for item in sources]
    return {
        "research": {
            "sources": sources,
            "key_points": key_points,
            "report": "111",
        }
    }

def validate_research(result: Dict[str, Any]) -> bool:
    research = result.get("research", {})
    return bool(research.get("sources")) and len(research.get("report", "")) > research_min_length


def writing_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    topic = state["topic"]
    length = state["length"]
    style = state["style"]
    research = state["research"]
    system_prompt = PROMPTS["write"].format(style=style, length=length)
    user_prompt = (
        f"主题：{topic}\n\n"
        f"研究报告：{research.get('report', '')}\n\n"
        f"参考来源：{research.get('sources', [])}"
    )
    draft = llm_client.generate(
        prompt=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    return {"draft": draft}

def validate_writing(result: Dict[str, Any]) -> bool:
    return len(result.get("draft", "")) >= draft_min_length


def review_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    draft = state["draft"]
    topic = state["topic"]
    system_prompt = PROMPTS["review"]

    user_prompt = f"""
    主题如下：\n{topic}\n\n
    文章如下：\n{draft}
    """

    text = llm_client.generate(
        prompt=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ],
    )
    json_data = json.loads(text)
    score = json_data.get("score", 0.0)
    issues = json_data.get("issues", [])

    return {
        "review": {
            "score": score,
            "issues": issues
        }
    }

def validate_review(result: Dict[str, Any]) -> bool:
    review = result.get("review", {})
    return review.get("score", 0.0) >= 0.7


def polishing_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    draft = state["draft"]
    review = state["review"]
    system_prompt = PROMPTS["polish"]
    user_prompt = f"文章：\n{draft}\n\n审核建议：\n{review}"
    final_article = llm_client.generate(
        prompt=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    return {"final_article": final_article}


def validate_polishing(result: Dict[str, Any]) -> bool:
    return len(result.get("final_article", "")) >= final_article_min_length


def fallback_review_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    draft = state.get("draft", "")
    score = 0.75 if len(draft) > 100 else 0.55
    issues = [] if score >= 0.7 else ["请补充更具体的事实或案例"]
    return {
        "review": {
            "score": score,
            "issues": issues,
            "advice": "补充事实依据，确保论证完整。",
        }
    }
