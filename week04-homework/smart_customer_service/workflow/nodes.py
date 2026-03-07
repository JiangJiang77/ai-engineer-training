"""LangGraph工作流节点实现

实现客服系统的各个处理节点
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_community.chat_models import ChatTongyi
from pydantic import BaseModel, Field

from smart_customer_service.workflow.state import CustomerServiceState, Intent
from smart_customer_service.workflow.order_query_service import (
    build_keyword,
    fetch_orders_by_context,
    format_orders,
)
from smart_customer_service.config import settings
from smart_customer_service.utils import parse_relative_time, get_logger
from smart_customer_service.client.ocr import extract_order_info_from_image
from smart_customer_service.client.asr import speech_to_text
from smart_customer_service.tools import (
    get_order_logistics,
    submit_refund,
    issue_invoice
)
from smart_customer_service.agents.react_agent import CustomerServiceReActAgent

logger = get_logger(__name__)


class ContextExtractResult(BaseModel):
    """上下文结构化提取结果"""

    time_expr: str = Field(default="", description="时间表达, 如 今天/昨天/前天/上周/本周")
    item: str = Field(default="", description="商品名称或品类, 如 手表/耳机")
    brand: str = Field(default="", description="品牌名称, 如 华为/Apple")


def _extract_context_by_llm(user_input: str) -> ContextExtractResult:
    """先用LLM提取上下文信息(JSON结构)"""
    parser = JsonOutputParser(pydantic_object=ContextExtractResult)
    prompt = PromptTemplate(
        template=(
            "你是电商客服的上下文信息提取器。\n"
            "请从用户输入中提取字段,并严格按 JSON 输出。\n"
            "字段要求:\n"
            "1) time_expr: 时间表达(例如 今天/昨天/前天/上周/本周), 没有则空字符串\n"
            "2) item: 商品名或品类(例如 手表/耳机), 没有则空字符串\n"
            "3) brand: 品牌名称(例如 华为/Apple), 没有则空字符串\n"
            "{format_instructions}\n\n"
            "用户输入: {user_input}"
        ),
        input_variables=["user_input"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    llm = ChatTongyi(
        model=settings.LLM_MODEL,
        temperature=0.1,
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
    )
    chain = prompt | llm | parser
    result = chain.invoke({"user_input": user_input})
    return ContextExtractResult(**result)


def _extract_order_id(user_input: str) -> str:
    """提取订单号

    优先使用正则识别, 如果结果模糊(多个匹配或无匹配)则调用LLM进行消歧或模糊识别
    """
    import re
    # UUID格式: 8-4-4-4-12 (例如: 33ca60d5-3d02-4df1-97f6-daba79a7e294)
    uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    # 简单字母数字组合
    simple_pattern = r'[A-Za-z0-9]{8,}'

    uuid_matches = re.findall(uuid_pattern, user_input)
    if len(set(uuid_matches)) == 1:
        logger.debug(f"✓ 正则提取唯一UUID: {uuid_matches[0]}")
        return uuid_matches[0]

    simple_matches = re.findall(simple_pattern, user_input)
    # 排除已识别出的UUID, 避免重复提取
    filtered_simple = [m for m in simple_matches if not any(m in u for u in uuid_matches)]

    if not uuid_matches and len(set(filtered_simple)) == 1:
        logger.debug(f"✓ 正则提取唯一简单单号: {filtered_simple[0]}")
        return filtered_simple[0]

    # 如果正则结果模糊(0个或多个), 使用LLM进行上下文识别
    logger.debug(f"正则识别模糊(UUID:{len(uuid_matches)}, 简单:{len(filtered_simple)}), 启动LLM消歧...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个订单号提取专家。
请从用户提供的文本中提取出最可能的订单号。

规则:
1. 优先提取UUID格式 (如 33ca60d5-3d02-4df1-97f6-daba79a7e294)
2. 结合上下文判断,排除快递单号或其他混淆ID
3. 如果识别到可能的模糊错误(如 'l' 误记为 '1'),尝试返回校准后的订单号
4. 只返回订单号本身,不要有任何多余文字
5. 如果实在无法识别,返回 "none" """),
        ("human", "{user_input}")
    ])

    llm = ChatTongyi(
        model=settings.LLM_MODEL,
        temperature=0.1,
        dashscope_api_key=settings.DASHSCOPE_API_KEY
    )

    chain = prompt | llm
    result = chain.invoke({"user_input": user_input})
    order_id = result.content.strip().lower()

    if order_id == "none":
        return None

    logger.debug(f"✓ LLM提取结果: {order_id}")
    return order_id



def input_preprocessing_node(state: CustomerServiceState) -> Dict[str, Any]:
    """输入预处理节点
    
    检测输入是否为文件路径(MP3或图片),并调用相应服务转文字
    """
    import os
    user_input = state["user_input"].strip()
    
    # 模拟终端交互模式下的路径输入
    # media/5551770796259_.pic.jpg 或者 media/2026021103594534377439.mp3
    
    lower_input = user_input.lower()
    processed_input = user_input
    
    logger.debug("-" * 60)
    logger.debug(f"进入输入预处理节点, 原始输入: {user_input}")
    
    # 判断是否是图片路径 (改为包含判断)
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    is_image = any(ext in lower_input for ext in image_extensions)
    
    # 判断是否是语音路径 (改为包含判断)
    is_audio = '.mp3' in lower_input
    
    if is_image:
        # 提取实际的图片路径 (取包含扩展名的那一部分)
        img_path = user_input
        for word in user_input.split():
            if any(word.lower().endswith(ext) for ext in image_extensions):
                img_path = word
                break
                
        logger.info(f"检测到图片输入, 开始OCR识别: {img_path}")
        try:
            order_info = extract_order_info_from_image(img_path)
            if "error" in order_info:
                logger.error(f"OCR识别失败: {order_info['error']}")
                processed_input = user_input.replace(img_path, f"[图片识别失败: {order_info['error']}]")
            else:
                # 提取订单号作为后续处理的输入
                order_id = order_info.get("order_id", "未知")
                order_name = order_info.get("order_name", "未知")
                # 将路径替换为识别出的订单信息,保留用户输入的其他文本(如 "开发票")
                order_desc = f"订单号 {order_id} ({order_name})"
                processed_input = user_input.replace(img_path, order_desc)
                logger.info(f"OCR识别成功, 替换结果: {processed_input}")
        except Exception as e:
            logger.error(f"OCR处理异常: {e}")
            processed_input = user_input.replace(img_path, f"[图片处理异常: {str(e)}]")
            
    elif is_audio:
        # 提取实际的语音路径
        audio_path = user_input
        for word in user_input.split():
            if word.lower().endswith('.mp3'):
                audio_path = word
                break
                
        logger.info(f"检测到语音输入, 开始ASR转换: {audio_path}")
        try:
            transcript = speech_to_text(audio_path)
            if transcript.startswith("识别失败") or transcript.startswith("识别出错"):
                logger.error(f"ASR转换失败: {transcript}")
                processed_input = user_input.replace(audio_path, "[语音转换失败]")
            else:
                # 将语音路径替换为转写文本
                processed_input = user_input.replace(audio_path, transcript)
                logger.info(f"ASR转换成功并替换: {processed_input}")
        except Exception as e:
            logger.error(f"ASR处理异常: {e}")
            processed_input = user_input.replace(audio_path, f"[语音处理异常: {str(e)}]")
    
    if processed_input != user_input:
        logger.info(f"输入预处理完成: {user_input} -> {processed_input}")
    else:
        logger.debug("输入无需预处理")
        
    logger.debug("-" * 60)
    
    return {
        "user_input": processed_input
    }


def intent_recognition_node(state: CustomerServiceState) -> Dict[str, Any]:
    """意图识别节点
    
    使用LLM识别用户意图
    """
    logger.debug("=" * 60)
    logger.debug("进入意图识别节点")
    logger.debug(f"用户输入: {state['user_input']}")
    logger.debug("=" * 60)
    
    # 构建意图识别提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能客服助手的意图识别模块。
        请根据用户输入,识别用户的意图。
        
        支持的意图类型:
        - orders_query: 订单查询
        - logistics_query: 物流查询(查看物流、发货状态等)
        - refund_application: 退款申请(退货、退款、申请退款等)
        - invoice_issuance: 发票开具(开发票、开具发票、要发票等)
        - policy_query: 政策查询(售后政策、退换货规则、物流政策、支付政策、质保政策、发票政策、发货时效等)
        - general_chat: 一般对话(问候、感谢等)
        - unknown: 未知意图(无法识别的请求)
        
        请只返回意图类型,不要有其他内容。"""),
        ("human", "{user_input}")
    ])
    
    # 调用LLM
    llm = ChatTongyi(
        model=settings.LLM_MODEL,
        temperature=0.1,  # 意图识别使用低温度
        dashscope_api_key=settings.DASHSCOPE_API_KEY
    )
    
    chain = prompt | llm
    result = chain.invoke({"user_input": state["user_input"]})
    
    intent = result.content.strip().lower()
    
    # 验证意图
    valid_intents = Intent.codes()
    
    if intent not in valid_intents:
        logger.warning(f"LLM返回了无效意图: {intent}, 设置为unknown")
        intent = Intent.UNKNOWN
    
    logger.debug(f"识别意图: {intent}")
    logger.debug("=" * 60)
    
    return {
        "intent": intent,
        "messages": [AIMessage(content=f"[意图识别: {intent}]")]
    }


def context_management_node(state: CustomerServiceState) -> Dict[str, Any]:
    """上下文管理节点
    
    提取和管理对话上下文信息
    """
    logger.debug("=" * 60)
    logger.debug("进入上下文管理节点")
    logger.debug(f"当前意图: {state.get('intent')}")
    logger.debug("=" * 60)
    
    context = state.get("context", {})
    user_input = state["user_input"]

    # 1) 优先用LLM结构化提取上下文
    extracted = ContextExtractResult()
    try:
        extracted = _extract_context_by_llm(user_input)
        logger.debug(
            "LLM上下文提取成功: time_expr=%s, item=%s, brand=%s",
            extracted.time_expr,
            extracted.item,
            extracted.brand,
        )
    except Exception as e:
        logger.error(f"LLM上下文提取失败, 将回退规则提取: {e}")

    # 2) 时间表达 -> time解析工具
    if extracted.time_expr:
        try:
            parsed_time = parse_relative_time(extracted.time_expr)
            context["date"] = parsed_time.date()
            context["date_str"] = extracted.time_expr
            logger.debug(f"✓ 解析时间: {extracted.time_expr} -> {context['date']}")
        except Exception as e:
            logger.error(f"✗ LLM时间解析失败: {e}")

    # 3) item/brand 结构化结果写入上下文
    if extracted.item:
        context["item"] = extracted.item
    if extracted.brand:
        context["brand"] = extracted.brand

    # 兼容现有工具参数: keyword 优先使用 item, 否则 brand
    if extracted.item:
        context["keyword"] = extracted.item
    elif extracted.brand:
        context["keyword"] = extracted.brand

    if "keyword" not in context:
        keywords = ["年货", "礼品", "大礼包", "手表", "电脑", "耳机", "笔记本"]
        for keyword in keywords:
            if keyword in user_input:
                context["keyword"] = keyword
                logger.debug(f"✓ 规则提取关键字: {keyword}")
                break

    # 提取订单号
    order_id = _extract_order_id(user_input)
    if order_id:
        context["order_id"] = order_id

    
    # 判断是否需要更多信息
    intent = state.get("intent")
    need_more_info = False

    if intent == Intent.LOGISTICS_QUERY:
        # 订单查询: order_id/keyword/item/brand 全空时需要追问
        need_more_info = not any(
            [
                context.get("order_id"),
                context.get("keyword"),
                context.get("item"),
                context.get("brand"),
            ]
        )
        logger.debug(
            "物流查询: %s",
            "关键信息缺失,需要追问" if need_more_info else "已提供查询条件,可继续处理",
        )
    elif intent == Intent.REFUND_APPLICATION:
        # 退款必须提供订单号
        need_more_info = not bool(context.get("order_id"))
    elif intent == Intent.INVOICE_ISSUANCE:
        # 发票必须提供订单号
        need_more_info = not bool(context.get("order_id"))
    
    logger.debug(f"上下文提取完成: {context}")
    logger.debug(f"需要更多信息: {need_more_info}")
    logger.debug("=" * 60)
    
    return {
        "context": context,
        "need_more_info": need_more_info
    }


def logistics_query_node(state: CustomerServiceState) -> Dict[str, Any]:
    """物流查询节点"""
    logger.debug("=" * 60)
    logger.debug("进入物流查询节点")
    logger.debug(f"用户输入: {state['user_input']}")
    logger.debug(f"上下文: {state['context']}")
    logger.debug("=" * 60)
    
    context = state["context"]
    user_id = state["user_id"]
    keyword = build_keyword(context)
    order_date = context.get("date")

    try:
        # 场景0: 有订单号时优先精确查询
        if context.get("order_id"):
            logger.debug(f"场景0: 订单号精确查询({context['order_id']})")
            result = get_order_logistics.invoke({
                "order_id": context["order_id"]
            })
            response = result

        else:
            # 场景1: 关键字 + 日期
            if keyword and order_date:
                logger.debug(f"场景1: 关键字({keyword}) + 日期({context.get('date_str')})")
                orders = fetch_orders_by_context(user_id, context)
                if not orders:
                    response = f"未找到 {context.get('date_str', '该日期')} 包含\"{keyword}\"的订单。"
                else:
                    response = (
                        f"找到 {len(orders)} 个 {context.get('date_str', '该日期')} "
                        f"包含\"{keyword}\"的订单:\n\n" + format_orders(orders)
                    )

            # 场景2: 仅关键字
            elif keyword:
                logger.debug(f"场景2: 仅关键字查询({keyword})")
                orders = fetch_orders_by_context(
                    user_id, context, include_date=False, include_keyword=True
                )
                if not orders:
                    response = f"未找到包含\"{keyword}\"的订单。"
                else:
                    response = f"找到 {len(orders)} 个包含\"{keyword}\"的订单:\n\n" + format_orders(orders)

            # 场景3: 仅日期
            elif order_date:
                logger.debug(f"场景3: 日期查询({context.get('date_str')})")
                orders = fetch_orders_by_context(
                    user_id, context, include_date=True, include_keyword=False
                )
                if not orders:
                    response = f"{context.get('date_str', '该日期')}没有订单。"
                else:
                    response = (
                        f"{context.get('date_str', '该日期')}共有 {len(orders)} 个订单:\n\n"
                        + format_orders(orders)
                    )

            # 场景4: 无筛选条件，列举所有订单
            else:
                logger.debug("场景4: 无筛选条件，返回追问提示")
                response = (
                    "请补充提前以下信息（至少一项）：时间、商品名、品牌名或订单号。"
                )

        logger.debug(f"物流查询结果(前100字符): {response[:100]}...")
        logger.debug("=" * 60)
        
        return {
            "response": response,
            "next_action": "end"
        }
    
    except Exception as e:
        logger.error(f"物流查询失败: {e}", exc_info=True)
        return {
            "response": f"查询订单时出错: {str(e)}",
            "next_action": "end"
        }


def refund_processing_node(state: CustomerServiceState) -> Dict[str, Any]:
    """退款处理节点"""
    logger.debug("退款处理节点")
    
    user_id = state["user_id"]
    context = state["context"]
    
    try:
        # 如果有订单号,直接提交退款
        if "order_id" in context:
            result = submit_refund.invoke({
                "order_id": context["order_id"]
            })
            response = result
        else:
            # 查询可退款订单(支持关键字过滤)
            orders = fetch_orders_by_context(
                user_id,
                context,
                include_keyword=True,
                include_date=False,
                extra_filters={"can_refund": 1},
            )
            if not orders:
                response = "没有可退款的订单。"
            else:
                response = (
                    f"可退款订单:\n{format_orders(orders)}\n\n"
                    "请提供订单号以继续退款申请。"
                )
        
        logger.debug(f"退款处理结果: {response[:100]}...")
        
        return {
            "response": response,
            "next_action": "end"
        }
    
    except Exception as e:
        logger.error(f"退款处理失败: {e}")
        return {
            "response": f"处理退款时出错: {str(e)}",
            "next_action": "end"
        }


def invoice_processing_node(state: CustomerServiceState) -> Dict[str, Any]:
    """发票处理节点"""
    
    
    user_id = state["user_id"]
    context = state["context"]
    logger.debug(f"发票处理节点({context})")
    
    try:
        # 如果有订单号,直接开具发票
        if "order_id" in context:
            result = issue_invoice.invoke({
                "order_id": context["order_id"]
            })
            response = result
        else:
            # 查询可开票订单
            orders = fetch_orders_by_context(
                user_id,
                context,
                include_keyword=True,
                include_date=False,
                extra_filters={"can_invoice": 1, "status": "delivered"},
            )
            if not orders:
                response = "没有可开票的订单(只有已签收的订单才能开具发票)。"
            else:
                response = (
                    f"可开票订单:\n{format_orders(orders)}\n\n"
                    "请提供订单号以继续开具发票。"
                )
        
        logger.debug(f"发票处理结果: {response[:100]}...")
        
        return {
            "response": response,
            "next_action": "end"
        }
    
    except Exception as e:
        logger.error(f"发票处理失败: {e}")
        return {
            "response": f"处理发票时出错: {str(e)}",
            "next_action": "end"
        }


def agent_tool_call_node(state: CustomerServiceState) -> Dict[str, Any]:
    """Agent工具调用节点

    使用ReAct Agent执行工具调用并生成最终回复。
    """
    logger.debug("Agent工具调用节点")
    user_id = state["user_id"]

    try:
        agent = CustomerServiceReActAgent(user_id=user_id, verbose=False)
        result = agent.run_by_state(state)
        response = result.get("output", "抱歉,我无法处理您的请求。")
        return {
            "response": response,
            "next_action": "end",
        }
    except Exception as e:
        logger.error(f"Agent工具调用失败: {e}", exc_info=True)
        return {
            "response": f"抱歉,处理您的请求时出错: {str(e)}",
            "next_action": "end",
        }


def llm_response_node(state: CustomerServiceState) -> Dict[str, Any]:
    """LLM生成回复节点
    
    用于一般对话和未知意图的处理
    """
    logger.debug("LLM生成回复节点")
    
    intent = state.get("intent")
    
    if intent == Intent.GENERAL_CHAT:
        # 一般对话
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个友好的智能客服助手。请简短回复用户。"),
            ("human", "{user_input}")
        ])
    else:
        # 未知意图
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个智能客服助手。用户的请求暂不支持,请友好地告知用户当前支持的功能。"),
            ("human", "{user_input}")
        ])
    
    llm = ChatTongyi(
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        dashscope_api_key=settings.DASHSCOPE_API_KEY
    )
    
    chain = prompt | llm
    result = chain.invoke({"user_input": state["user_input"]})
    
    response = result.content
    
    logger.debug(f"LLM回复: {response[:100]}...")
    
    return {
        "response": response,
        "next_action": "end"
    }


def policy_retrieval_node(state: CustomerServiceState) -> Dict[str, Any]:
    """政策检索节点
    
    使用RAG检索相关政策并生成回答
    """
    logger.debug("=" * 60)
    logger.debug("进入政策检索节点")
    logger.debug(f"用户输入: {state['user_input']}")
    logger.debug("=" * 60)
    
    try:
        # 导入RAG模块
        from smart_customer_service.rag import load_documents, VectorStoreManager
        
        # 初始化向量存储管理器
        vector_store_manager = VectorStoreManager()
        
        # 尝试加载或创建向量存储
        if not vector_store_manager.load_vectorstore():
            logger.debug("向量存储不存在,开始加载文档并创建")
            documents = load_documents()
            if not documents:
                return {
                    "response": "抱歉,政策文档加载失败,无法回答您的问题。",
                    "next_action": "end"
                }
            vector_store_manager.create_vectorstore(documents)
        
        # 执行相似度搜索
        query = state["user_input"]
        retrieved_docs = vector_store_manager.similarity_search(query, k=3)
        
        if not retrieved_docs:
            return {
                "response": "抱歉,没有找到相关的政策信息。",
                "next_action": "end"
            }
        
        # 格式化检索结果
        context = "\n\n".join([
            f"【{doc.metadata.get('type', '文档')}】\n{doc.page_content}"
            for doc in retrieved_docs
        ])
        
        logger.debug(f"检索到 {len(retrieved_docs)} 个相关文档片段")
        
        # 使用LLM基于检索内容生成回答
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的智能客服助手。
请根据以下政策文档内容,回答用户的问题。

政策文档内容:
{context}

要求:
1. 只基于提供的文档内容回答
2. 回答要准确、完整、易懂
3. 如果文档中没有相关信息,请明确告知用户
4. 使用友好、专业的语气"""),
            ("human", "{question}")
        ])
        
        llm = ChatTongyi(
            model=settings.LLM_MODEL,
            temperature=0.3,  # 政策查询使用较低温度
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )
        
        chain = prompt | llm
        result = chain.invoke({
            "context": context,
            "question": query
        })
        
        response = result.content
        
        logger.debug(f"政策检索回复(前100字符): {response[:100]}...")
        logger.debug("=" * 60)
        
        return {
            "retrieved_docs": context,
            "response": response,
            "next_action": "end"
        }
    
    except Exception as e:
        logger.error(f"政策检索失败: {e}", exc_info=True)
        return {
            "response": f"抱歉,查询政策时出错: {str(e)}",
            "next_action": "end"
        }
