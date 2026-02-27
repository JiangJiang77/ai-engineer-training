"""LangGraph工作流节点实现

实现客服系统的各个处理节点
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi

from smart_customer_service.workflow.state import CustomerServiceState, Intent, NodeName
from smart_customer_service.config import settings
from smart_customer_service.utils import parse_relative_time, get_logger
from smart_customer_service.utils.ocr import extract_order_info_from_image
from smart_customer_service.utils.asr import speech_to_text
from smart_customer_service.tools import (
    query_order_by_keyword,
    query_orders_by_date,
    get_order_logistics,
    query_refundable_orders,
    submit_refund,
    query_invoiceable_orders,
    issue_invoice
)

logger = get_logger(__name__)


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
- logistics_query: 物流查询(查询订单、查看物流、发货状态、列举订单、我的订单等)
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
    valid_intents = [
        Intent.LOGISTICS_QUERY,
        Intent.REFUND_APPLICATION,
        Intent.INVOICE_ISSUANCE,
        Intent.POLICY_QUERY,
        Intent.GENERAL_CHAT,
        Intent.UNKNOWN
    ]
    
    if intent not in valid_intents:
        logger.warning(f"LLM返回了无效意图: {intent}, 设置为unknown")
        intent = Intent.UNKNOWN
    
    logger.info(f"识别意图: {intent}")
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
    
    # 解析时间表达
    time_keywords = ["昨天", "今天", "前天", "明天", "上周", "本周"]
    for keyword in time_keywords:
        if keyword in user_input:
            try:
                parsed_time = parse_relative_time(keyword)
                context["date"] = parsed_time.date()
                context["date_str"] = keyword
                logger.debug(f"✓ 解析时间: {keyword} -> {context['date']}")
            except Exception as e:
                logger.error(f"✗ 时间解析失败: {e}")
    
    # 提取关键字(优化:支持部分匹配)
    keywords = ["年货", "礼品", "大礼包", "手表", "电脑", "耳机", "笔记本"]
    for keyword in keywords:
        if keyword in user_input:
            context["keyword"] = keyword
            logger.debug(f"✓ 提取关键字: {keyword}")
            break
    
    # 提取订单号
    order_id = _extract_order_id(user_input)
    if order_id:
        context["order_id"] = order_id

    
    # 判断是否需要更多信息
    intent = state.get("intent")
    need_more_info = False
    
    if intent == Intent.LOGISTICS_QUERY:
        # 物流查询:如果没有任何筛选条件,也可以列举所有订单
        # 所以不需要追问
        need_more_info = False
        logger.debug("物流查询: 可以无条件列举订单,不需要追问")
    elif intent == Intent.REFUND_APPLICATION:
        # 退款需要订单号(可以后续查询列表)
        pass
    elif intent == Intent.INVOICE_ISSUANCE:
        # 发票需要订单号(可以后续查询列表)
        pass
    
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
    
    # 订单状态中文映射
    STATUS_MAP = {
        "pending": "待处理",
        "shipped": "已发货",
        "delivered": "已签收",
        "cancelled": "已取消"
    }
    
    context = state["context"]
    user_id = state["user_id"]
    
    try:
        # 场景1: 有关键字和日期
        if "keyword" in context and "date" in context:
            logger.debug(f"场景1: 关键字({context['keyword']}) + 日期({context.get('date_str')})")
            result = query_order_by_keyword.invoke({
                "user_id": user_id,
                "keyword": context["keyword"],
                "date_str": context.get("date_str", "昨天")
            })
            response = f"查询结果:\n{result}"
        
        # 场景1.5: 只有关键字(新增)
        elif "keyword" in context:
            logger.debug(f"场景1.5: 仅关键字查询({context['keyword']})")
            # 查询所有包含该关键字的订单
            from smart_customer_service.database import query_orders
            all_orders = query_orders(user_id)
            
            # 筛选包含关键字的订单
            keyword = context["keyword"]
            filtered_orders = [
                order for order in all_orders 
                if keyword in order.get("order_name", "")
            ]
            
            if not filtered_orders:
                response = f"未找到包含\"{keyword}\"的订单。"
            else:
                # 格式化订单列表
                order_list = []
                for order in filtered_orders:
                    order_date = order["order_date"]
                    if hasattr(order_date, 'strftime'):
                        order_date = order_date.strftime("%Y-%m-%d")
                    # 显示完整订单号,状态翻译成中文
                    status_cn = STATUS_MAP.get(order["status"], order["status"])
                    order_list.append(
                        f"- 订单号: {order['order_id']}\n"
                        f"  商品: {order['order_name']}\n"
                        f"  日期: {order_date}\n"
                        f"  状态: {status_cn}\n"
                        f"  物流: {order.get('logistics_status', '暂无物流信息')}\n"
                        f"  发票: {order.get('invoice_status', '未开票')}"
                    )
                response = f"找到 {len(filtered_orders)} 个包含\"{keyword}\"的订单:\n\n" + "\n\n".join(order_list)
        
        # 场景2: 只有日期
        elif "date" in context:
            logger.debug(f"场景2: 日期查询({context.get('date_str')})")
            result = query_orders_by_date.invoke({
                "user_id": user_id,
                "date_str": context.get("date_str", "昨天")
            })
            response = f"查询结果:\n{result}"
        
        # 场景3: 有订单号
        elif "order_id" in context:
            logger.debug(f"场景3: 订单号查询({context['order_id']})")
            result = get_order_logistics.invoke({
                "order_id": context["order_id"]
            })
            response = result
        
        # 场景4: 无条件列举所有订单
        else:
            logger.debug("场景4: 列举所有订单(无筛选条件)")
            from smart_customer_service.database import query_orders
            orders = query_orders(user_id)
            
            if not orders:
                response = "您还没有任何订单。"
            else:
                # 格式化订单列表
                order_list = []
                for order in orders:
                    order_date = order["order_date"]
                    if hasattr(order_date, 'strftime'):
                        order_date = order_date.strftime("%Y-%m-%d")
                    # 显示完整订单号,状态翻译成中文
                    status_cn = STATUS_MAP.get(order["status"], order["status"])
                    order_list.append(
                        f"- 订单号: {order['order_id']}\n"
                        f"  商品: {order['order_name']}\n"
                        f"  日期: {order_date}\n"
                        f"  状态: {status_cn}\n"
                        f"  发票: {order.get('invoice_status', '未开票')}"
                    )
                response = f"您共有 {len(orders)} 个订单:\n\n" + "\n\n".join(order_list)
        
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
            # 查询可退款订单
            result = query_refundable_orders.invoke({
                "user_id": user_id
            })
            response = f"可退款订单:\n{result}\n\n请提供订单号以继续退款申请。"
        
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
            keyword = context.get("keyword")
            result = query_invoiceable_orders.invoke({
                "user_id": user_id,
                "keyword": keyword
            })
            response = f"可开票订单:\n{result}\n\n请提供订单号以继续开具发票。"
        
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

