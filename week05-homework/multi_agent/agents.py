import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from multi_agent.llm import llm_client
from multi_agent.tools.search_tool import search_tool
from multi_agent.prompts import PROMPTS

research_min_length = 300
draft_min_length = 10
fallback_score = 0.75
final_article_min_length = 200
valid_review_stages = {"initial", "recheck"}
review_stage_aliases = {
    "peer": "initial",
    "editor": "initial",
    "final": "recheck",
}


def normalize_review_stage(stage: str) -> str:
    mapped = review_stage_aliases.get(stage, stage)
    if mapped not in valid_review_stages:
        return "initial"
    return mapped

def research_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    topic = state["topic"]
    sources = search_tool(topic)
    system_prompt = PROMPTS["research"]
    user_prompt = (
        f"主题：{topic}\n\n"
        f"搜索结果：{sources}\n\n"
        f"请基于以上结果输出研究报告,不少于 {research_min_length} 字。"
    )
    report = llm_client.generate(
        prompt=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )

    key_points = [item["summary"] for item in sources]
    return {
        "research": {
            "sources": sources,
            "key_points": key_points,
            "report": report,
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
    review = state.get("review", {})
    review_stage = normalize_review_stage(str(state.get("review_stage", "initial")))
    review_requirements = state.get("review_requirements", [])
    previous_draft = state.get("draft", "")
    system_prompt = PROMPTS["write"].format(style=style, length=length)
    base_prompt = (
        f"主题：{topic}\n\n"
        f"研究报告：{research.get('report', '')}\n\n"
        f"参考来源：{research.get('sources', [])}"
    )
    is_rewrite = bool(review) and not review.get("passed", True)
    if is_rewrite:
        user_prompt = (
            f"{base_prompt}\n\n"
            f"当前评审阶段：{review_stage}\n\n"
            f"上一版文章：\n{previous_draft}\n\n"
            f"问题清单：{review.get('issues', [])}\n\n"
            f"修改要求：{review_requirements}\n\n"
            "请逐条落实问题和修改要求，输出完整改写稿。"
        )
    else:
        user_prompt = base_prompt

    if is_rewrite:
        draft = llm_client.generate(
            prompt=[
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
    else:
        draft = "这是粗糙的初版文章，用于测试重写逻辑是否生效。"

    
    return {"draft": draft}

def validate_writing(result: Dict[str, Any]) -> bool:
    return len(result.get("draft", "")) >= draft_min_length


def review_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    draft = state["draft"]
    topic = state["topic"]
    review_stage = normalize_review_stage(str(state.get("review_stage", "initial")))
    stage_focus = {
        "initial": "重点审查结构、逻辑、证据、方法的专业性和严谨性。",
        "recheck": "重点逐条核对前一轮问题是否已被解决，并指出残留问题。",
    }
    system_prompt = PROMPTS["review"]

    user_prompt = f"""
    当前评审阶段：{review_stage}
    阶段要求：{stage_focus.get(review_stage, stage_focus["initial"])}

    主题如下：\n{topic}\n\n
    文章如下：\n{draft}\n\n
    上一轮问题清单：{state.get("review", {}).get("issues", [])}
    上一轮修改要求：{state.get("review_requirements", [])}

    请严格输出 JSON，格式如下：
    {{
      "score": 0.0-1.0 的分数,
      "issues": ["问题1", "问题2"],
      "requirements": ["修改要求1", "修改要求2"],
      "passed": true/false,
      "stage": "{review_stage}"
    }}
    """

    text = llm_client.generate(
        prompt=[
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ],
    )
    json_data = json.loads(text)
    score = float(json_data.get("score", 0.0))
    issues = json_data.get("issues", [])
    requirements = json_data.get("requirements", [])
    if not isinstance(issues, list):
        issues = [str(issues)]
    if not isinstance(requirements, list):
        requirements = [str(requirements)]
    stage = normalize_review_stage(str(json_data.get("stage", review_stage)))
    passed = bool(json_data.get("passed", score >= 0.7))

    return {
        "review": {
            "score": score,
            "issues": issues,
            "requirements": requirements,
            "passed": passed,
            "stage": stage,
        }
    }

def validate_review(result: Dict[str, Any]) -> bool:
    review = result.get("review", {})
    return (
        isinstance(review, dict)
        and isinstance(review.get("score", 0.0), (int, float))
        and isinstance(review.get("issues", []), list)
        and isinstance(review.get("requirements", []), list)
        and isinstance(review.get("passed", False), bool)
        and str(review.get("stage", "")) in valid_review_stages
    )


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
    review_stage = normalize_review_stage(str(state.get("review_stage", "initial")))
    score = 0.75 if len(draft) > 100 else 0.55
    issues = [] if score >= 0.7 else ["请补充更具体的事实或案例"]
    requirements = [] if score >= 0.7 else ["补充可核验的数据来源并强化论证逻辑"]
    return {
        "review": {
            "score": score,
            "issues": issues,
            "requirements": requirements,
            "passed": score >= 0.7,
            "stage": review_stage,
        }
    }
