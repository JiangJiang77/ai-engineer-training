
import os
import operator
import json
from dotenv import load_dotenv
from typing import Annotated, Sequence, Literal, TypedDict
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain.agents import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from urllib3 import response

from .services import ServiceManager


load_dotenv()


class AgentState(TypedDict):
    intent: str
    order_id: str
    messages: Annotated[Sequence[BaseMessage], operator.add]

class GraphManager:
    def __init__(self, service_manager: ServiceManager):
        self._service_manager = service_manager
        self._compiled_graph= self._build_graph()


    def _build_graph(self):

        workflow = StateGraph(AgentState)

        # chatbot
        workflow.add_node("intent_recognition",self._intent_recognition)
        workflow.add_node("ask_order_id",self._ask_order_id)
        workflow.add_node("ask_invoice_info",self._ask_invoice_info)
        workflow.add_node("tool_agent", self._call_tool_agent)
        tools = ToolNode(tools=self._service_manager.get_tools())
        workflow.add_node("tools", tools)
        workflow.add_node("chat_bot",self._call_chat_bot)

        
        workflow.add_edge(START, "intent_recognition")

        workflow.add_conditional_edges("intent_recognition", self._router_intent,
        {
            "tool_agent": "tool_agent",
            "ask_order_id": "ask_order_id",
            "ask_invoice_info": "ask_invoice_info",
        })
        ## ask_order_id tool_agent

        workflow.add_edge("ask_order_id", END)

        workflow.add_conditional_edges(
            "tool_agent",
            self._should_continue,
            {
                "tools": "tools",
                "chat_bot": "chat_bot",
            },
        )
        workflow.add_edge("tools", "chat_bot")
        workflow.add_edge("chat_bot", END)

        checkpointer = InMemorySaver()
        compiled_graph = workflow.compile(checkpointer=checkpointer)
        print("✅ LangGraph graph built/rebuilt successfully!")
        # print_workflow_graph(compiled_graph)
        return compiled_graph

    def _intent_recognition(self, user_input: str):
        """
        意图识别
        """
        prompt = ChatPromptTemplate.from_messages([
                ("system", 
                """你是一个智能客服助手的意图识别模块。
                请根据用户输入,识别用户的意图。
                
                支持的意图类型:
                - orders_query: 订单查询
                - policy_query: 政策查询(售后政策、退换货规则、物流政策、支付政策、质保政策、发票政策、发货时效等)
                - generate_invoice: 开具发票
                - unknown: 未知意图(无法识别的请求)
                
                请只返回意图类型,不要有其他内容。"""),
            ("human", "{user_input}")
        ])
        chain = prompt | self._service_manager.get_llm()
        result = chain.invoke({
                "user_input": user_input
            })
        print(f"意图识别结果: {result.content}")
        return {"messages": [AIMessage(content=result.content)],"intent": result.content}


    def _call_chat_bot(self,state: AgentState):
        """
        生成客服回复
        """
        user_input = self._get_latest_user_input(state)

        state["messages"][-1]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业友好智能客服助手的回复模块。
            请结合 用户输入和 tool调用结果 生成客服回复。
            不要回复不存在的内容
            """),
            ("human", "{user_input}")
        ])
        chain = prompt | self._service_manager.get_llm()
        result = chain.invoke({
            "user_input": user_input
        })
        
        return {"messages": [AIMessage(content=result.content)]}

    def _ask_order_id(self,state: AgentState):
        """
        询问订单号
        """
        return {"messages": [AIMessage(content="请提供订单号")]}

    def _ask_invoice_info(self,state: AgentState):
        """
        询问发票信息
        """
        return {"messages": [AIMessage(content="请提供发票信息(订单号、姓名、税号)")]}

    def _router_intent(self,state: AgentState):
        """
        路由意图
        """
        intent = state["messages"][-1].content
        if intent == "orders_query":
            user_input = self._get_latest_user_input(state)
            order_id = self._extra_order_id(user_input)
            if user_input and order_id:
                return "tool_agent"
            return "ask_order_id"
        elif intent == "generate_invoice":
            user_input = self._get_latest_user_input(state)
            invoice_info = self._extra_invoice_info(user_input)
            if user_input and invoice_info.get("order_id"):
                return "tool_agent"
            return "ask_invoice_info"
        return "tool_agent"
    
    def _router_order(self,state: AgentState):
        """
        路由订单查询
        """
        order_id = state.order_id
        if order_id :
            return "tool"
        return "ask_order_id"

    def _get_latest_user_input(self,state) -> str:
        messages = state['messages']
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return str(msg.content).strip()
        return ""
        
    def _extra_order_id(self, user_input: str):
        """
        订单号提取
        """
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
        chain = prompt | self._service_manager.get_llm()
        result = chain.invoke({
                "user_input": user_input
            })
        order_id = result.content.strip()
        if order_id.lower() in {"none", "无法提取订单号", ""}:
            return None
        print(f"提取到的订单号: {order_id}")
        return order_id


    def _extra_invoice_info(self, user_input: str):
        """
        发票信息提取
        """
        import re

        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个发票信息提取器。请从用户输入中提取: order_id, name, tax_number。

            输出要求(必须全部满足):
            1. 只输出一个 JSON 对象,不要 markdown、不要解释、不要多余文本。
            2. JSON 键固定为 "order_id"、"name"、"tax_number"。
            3. 值类型: 字符串或 null。无法确认时使用 null。
            4. 不要臆造信息,缺失就填 null。
            5. order_id 优先提取 UUID(8-4-4-4-12)；若有多个候选,选择最像订单号而非快递单号的那个。
            6. name 仅提取购方名称(个人/公司),不要混入地址电话。
            7. tax_number 仅提取纳税人识别号,保留字母数字,去掉空格。

            示例:
            {{"order_id":"33ca60d5-3d02-4df1-97f6-daba79a7e294","name":"张三","tax_number":"91330100MA2XXXXXX"}}
            {{"order_id":null,"name":"个人","tax_number":null}}
            """),
                ("human", "{user_input}")
            ])
        chain = prompt | self._service_manager.get_llm()
        result = chain.invoke({
                "user_input": user_input
            })
        raw_content = result.content.strip()

        # 兼容模型偶发返回 ```json ... ``` 或夹带说明文本
        candidate = raw_content.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{[\s\S]*\}", candidate)
        if match:
            candidate = match.group(0)

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            print(f"发票信息提取结果无法解析为JSON: {raw_content}")
            return None

        invoice_info = {
            "order_id": parsed.get("order_id"),
            "name": parsed.get("name"),
            "tax_number": parsed.get("tax_number"),
        }

        for key, value in invoice_info.items():
            if isinstance(value, str):
                normalized = value.strip()
                if normalized.lower() in {"none", "null", ""}:
                    invoice_info[key] = None
                else:
                    invoice_info[key] = normalized

        print(f"提取到的发票信息: {invoice_info}")
        return invoice_info
    
    def _call_tool_agent(self,state: AgentState):
        """
        工具代理
        """
        model_with_tools = self._service_manager.get_llm().bind_tools(self._service_manager.get_tools())
        response = model_with_tools.invoke(state['messages'])
        print(f"工具调用结果: {response.tool_calls[0]['name']}")
        return {"messages": [response]}

    def _should_continue(self,state: AgentState):
        """
        判断是否继续
        """
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

        return "chat_bot"

    def run_workflow(self, user_input: str, config: dict = None, stream_mode: bool = False):
        """
        运行工作流
        """
        # return self._compiled_graph.invoke({"messages": [HumanMessage(content=user_input)]})
        for event in self._compiled_graph.stream(
            {"messages": [HumanMessage(content=user_input)]}, 
            config=config, stream_mode=stream_mode):
            for value in event.values():
                print("Assistant:", value["messages"][-1].content)
    
    def invoke_workflow(self, user_input: str, config: dict = None):
        """
        运行工作流
        """
        result = self._compiled_graph.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
        # final_response = next(
        #     (m for m in reversed(result["messages"]) if isinstance(m, AIMessage) and not m.tool_calls),
        #     None,
        # )
        # return final_response.content if final_response else None

        messages = result['messages']
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
               return msg.content
        return None

    def reload_graph(self):
        self._compiled_graph = self._build_graph()
        print("✅ LangGraph Reload成功!")
        print_workflow_graph(self._compiled_graph)


def print_workflow_graph(compiled_graph):
    """打印工作流图流程图(Mermaid格式)并保存为图片"""
    print("\n" + "-" * 20 + " 工作流流程图 (Mermaid) " + "-" * 20)
    try:
        # 获取mermaid源码
        mermaid_code = compiled_graph.get_graph().draw_mermaid()
        print(mermaid_code)
        
        # 保存为图片
        try:
            # 确保media目录存在
            media_dir = "smart_customer_service"
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)
            
            # 使用 draw_mermaid_png 获取图片字节流
            png_data = compiled_graph.get_graph().draw_mermaid_png()
            file_path = os.path.join(media_dir, "smart_customer_service_workflow.png")
            
            with open(file_path, "wb") as f:
                f.write(png_data)
            print(f"\n[提示] 流程图已保存至: {file_path}")
        except Exception as img_e:
            # 可能是因为缺少 pygraphviz 或相关依赖, 静默失败或打印提示
            print(f"\n[提示] 自动保存图片失败 (可能缺少依赖): {img_e}")
            
    except Exception as e:
        print(f"无法生成流程图: {e}")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    graph = GraphManager(ServiceManager())
    # user_input = "你好，我想查询订单"
    user_input = "你好，我想查询订单,订单号是 dcc38dae-fe72-4e65-a419-7d87d29d603e"
    response = graph.run_workflow(user_input)
    print(response)
