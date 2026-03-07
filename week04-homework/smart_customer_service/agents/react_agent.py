"""ReAct Agent实现

基于LangGraph的ReAct Agent,具备推理和行动能力
"""
from langgraph.prebuilt import create_react_agent
from langchain_community.chat_models import ChatTongyi
from typing import Dict, Any

from smart_customer_service.config import settings
from smart_customer_service.utils import get_logger
from smart_customer_service.agents.tools import create_customer_service_tools
from smart_customer_service.workflow.state import CustomerServiceState,Intent

logger = get_logger(__name__)


class CustomerServiceReActAgent:
    """客服ReAct Agent
    
    使用ReAct(Reasoning + Acting)模式,通过推理选择合适的工具来解决用户问题
    """
    
    def __init__(self, user_id: str, verbose: bool = True):
        """
        初始化Agent
        
        Args:
            user_id: 用户ID
            verbose: 是否显示推理过程
        """
        self.user_id = user_id
        self.verbose = verbose
        
        logger.debug(f"初始化ReAct Agent: user_id={user_id}, verbose={verbose}")
        
        # 初始化LLM
        self.llm = ChatTongyi(
            model=settings.LLM_MODEL,
            temperature=0.1,  # 低温度保证稳定性
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )
        
        # 创建工具
        self.tools = create_customer_service_tools(user_id)
        
        # 系统指令(LangGraph会自动处理ReAct格式)
        system_prompt = f"""你是一个专业的智能客服助手,负责帮助用户处理订单相关问题。

            当前用户ID: {user_id}
            
            重要规则:
            1. 当工具返回的结果无法完全回答用户问题时,应该使用search_policy_tool工具补充相关政策信息
            
            智能补充策略(非常重要):
            - 当用户询问"什么时候发货"、"多久能到"等问题时:
              如果查询订单只返回了订单状态(如"pending"、"订单处理中"),这不足以回答"什么时候"
              应该继续调用search_policy_tool查询"发货时效"政策
              最终回答要结合订单状态和发货政策
            
            - 当用户询问"能退货吗"、"怎么退货"等问题时:
              如果查询订单只返回了"可退款:是",这不足以说明退货流程和规则
              应该继续调用search_policy_tool查询"退货政策"
              最终回答要包含退货条件、流程、时效等完整信息
            
            - 当用户询问"保修多久"、"质保期"等问题时:
              订单信息中通常没有保修期信息
              应该调用search_policy_tool查询"保修政策"
            
            判断标准:
            - 工具返回了数据,但数据不足以完整回答用户的问题
            - 用户问题包含"什么时候"、"多久"、"怎么办"、"能不能"等需要政策支持的疑问词
            - 用户询问的是规则、流程、时效、条件等政策性内容
            
            请始终提供友好、专业、完整的回答。"""
        
        # 创建ReAct Agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt
        )
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        执行Agent
        
        Args:
            user_input: 用户输入
            
        Returns:
            {
                "output": str,  # 最终回答
                "intermediate_steps": list,  # 中间步骤
                "iterations": int  # 迭代次数
            }
        """
        logger.debug(f"ReAct Agent开始处理: input={user_input}")
        
        try:
            result = self.agent.invoke({
                "messages": [("user", user_input)]
            })
            
            # 从messages中提取最终回答
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                output = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                output = "抱歉,我无法处理您的请求"
            
            # 计算迭代次数(messages中AI消息的数量)
            iterations = sum(1 for msg in messages if hasattr(msg, 'type') and msg.type == 'ai')
            
            logger.debug(f"ReAct Agent处理完成: iterations={iterations}")

            for i, msg in enumerate(messages):
                msg_type = getattr(msg, "type", type(msg).__name__)
                content = getattr(msg, "content", str(msg))
                logger.debug(f"[ReAct Message {i}] type={msg_type} content={content}")
            
            return {
                "output": output,
                "intermediate_steps": messages,
                "iterations": iterations
            }
            
        except Exception as e:
            logger.error(f"ReAct Agent执行失败: {e}", exc_info=True)
            return {
                "output": f"抱歉,处理您的请求时出错: {str(e)}",
                "intermediate_steps": [],
                "iterations": 0
            }

    def run_by_state(self, state: CustomerServiceState) -> Dict[str, Any]:
        """
        执行Agent

        Args:
            user_input: 用户输入

        Returns:
            {
                "output": str,  # 最终回答
                "intermediate_steps": list,  # 中间步骤
                "iterations": int  # 迭代次数
            }
        """
        user_id = state["user_id"]
        user_input = state["user_input"]
        intent = state["intent"]
        intent_name = Intent.name_for(intent)
        context = state["context"]
        logger.debug(f"ReAct Agent开始处理: user_id={user_id}, user_input={user_input}, intent={intent}")

        try:
            messages_input=[]
            if intent:
                messages_input.append((
                        "system",
                        f"当前已识别意图: {intent_name}。"
                        "结合用户意图分析，调用对应工具"
                    ))
            if context:
                messages_input.append((
                    "system",
                    f"当前已识别上下文信息: {context}。"
                ))


            result = self.agent.invoke({ "messages": messages_input})

            # 从messages中提取最终回答
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                output = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                output = "抱歉,我无法处理您的请求"

            # 计算迭代次数(messages中AI消息的数量)
            iterations = sum(1 for msg in messages if hasattr(msg, 'type') and msg.type == 'ai')

            logger.debug(f"ReAct Agent处理完成: iterations={iterations}")

            for i, msg in enumerate(messages):
                msg_type = getattr(msg, "type", type(msg).__name__)
                content = getattr(msg, "content", str(msg))
                logger.debug(f"[ReAct Message {i}] type={msg_type} content={content}")

            return {
                "output": output,
                "intermediate_steps": messages,
                "iterations": iterations
            }

        except Exception as e:
            logger.error(f"ReAct Agent执行失败: {e}", exc_info=True)
            return {
                "output": f"抱歉,处理您的请求时出错: {str(e)}",
                "intermediate_steps": [],
                "iterations": 0
            }
    
    def run_simple(self, user_input: str) -> str:
        """
        简化版执行,只返回最终回答
        
        Args:
            user_input: 用户输入
            
        Returns:
            最终回答
        """
        result = self.run(user_input)
        return result["output"]
