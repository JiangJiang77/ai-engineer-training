import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_community.chat_models import ChatTongyi


load_dotenv()


def _create_llm(
                model_name: str | None = None,
                temperature: float  = 0,
                streaming: bool =True):
    if not os.environ.get("DASHSCOPE_API_KEY"):
        print("⚠️ 警告: DASHSCOPE_API_KEY 环境变量未设置！")
    return ChatTongyi(
        model_name=model_name or "qwen-plus",
        temperature=temperature,
        streaming=streaming,
    )

def demo_llm_chain():
    """
    演示 LLMChain：支持变量注入与模板复用的核心组件
    LangChain 特点：模板化提示词管理，支持变量替换
    """
    print("=" * 50)
    print("🔗 LLMChain 演示：Prompt → LLM → 输出链")
    print("=" * 50)
    
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

    str_prompt = ChatPromptTemplate.from_messages([
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

    llm = _create_llm("qwen-plus",0,False)
    chain = prompt | llm
    result = chain.invoke({"user_input": "我想查询订单状态"})
    print(result.content)

def demo_llm_chain_streaming():
    """ 
    演示 LLMChain：支持变量注入与模板复用的核心组件
    LangChain 特点：模板化提示词管理，支持变量替换
    """
    print("=" * 50)
    print("🔗 LLMChain 演示：Prompt → LLM → 输出链")
    print("=" * 50)
    

    prompt = PromptTemplate.from_template("""你是一个专业的机器人产品专家，请编写最前沿的机器人产品洞察报告，
    报告内容包括：机器人产品的发展趋势、机器人产品的技术特点、机器人产品的市场应用、机器人产品的未来发展方向等。500 字以内""")

    llm = _create_llm("qwen-plus",0,True)
    chain = prompt | llm
    
    for chunk in chain.stream({}):
        print(chunk.content, end="", flush=True)
    print()


def demo_llm_chain_not_streaming():
    """ 
    演示 LLMChain：支持变量注入与模板复用的核心组件
    LangChain 特点：模板化提示词管理，支持变量替换
    """
    print("=" * 50)
    print("🔗 LLMChain 演示：Prompt → LLM → 输出链")
    print("=" * 50)
    

    prompt = PromptTemplate.from_template("""你是一个专业的机器人产品专家，请编写最前沿的机器人产品洞察报告，
    报告内容包括：机器人产品的发展趋势、机器人产品的技术特点、机器人产品的市场应用、机器人产品的未来发展方向等。500 字以内""")

    llm = _create_llm("qwen-plus",0,False)
    chain = prompt | llm
    result = chain.invoke({"user_input": "我想查询订单状态"})
    print(result.content)

if __name__ == "__main__":
    # demo_llm_chain()
    demo_llm_chain_streaming()
    demo_llm_chain_not_streaming()