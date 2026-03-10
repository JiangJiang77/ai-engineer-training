import unittest

from langchain_core.messages import AIMessage, HumanMessage

from tests.langgraph_demo._stub_reportlab import install_reportlab_stub

install_reportlab_stub()

from langgraph_demo.graph import GraphManager


class TestGraphRouting(unittest.TestCase):
    def setUp(self):
        # 只测试路由逻辑, 不构建真实 graph/llm
        self.graph = object.__new__(GraphManager)

    def test_orders_query_with_order_id_routes_tool_agent(self):
        self.graph._extra_order_id = lambda _: "o-123"
        self.graph._extra_invoice_info = lambda _: None

        state = {"messages": [HumanMessage(content="查订单"), AIMessage(content="orders_query")]}
        route = self.graph._router_intent(state)
        self.assertEqual(route, "tool_agent")

    def test_orders_query_without_order_id_routes_ask_order_id(self):
        self.graph._extra_order_id = lambda _: None
        self.graph._extra_invoice_info = lambda _: None

        state = {"messages": [HumanMessage(content="查订单"), AIMessage(content="orders_query")]}
        route = self.graph._router_intent(state)
        self.assertEqual(route, "ask_order_id")

    def test_generate_invoice_with_order_id_routes_tool_agent(self):
        self.graph._extra_order_id = lambda _: None
        self.graph._extra_invoice_info = lambda _: {"order_id": "o-123", "name": "张三", "tax_number": None}

        state = {"messages": [HumanMessage(content="开发票"), AIMessage(content="generate_invoice")]}
        route = self.graph._router_intent(state)
        self.assertEqual(route, "tool_agent")

    def test_generate_invoice_without_order_id_routes_ask_invoice_info(self):
        self.graph._extra_order_id = lambda _: None
        self.graph._extra_invoice_info = lambda _: {"order_id": None, "name": "张三", "tax_number": None}

        state = {"messages": [HumanMessage(content="开发票"), AIMessage(content="generate_invoice")]}
        route = self.graph._router_intent(state)
        self.assertEqual(route, "ask_invoice_info")

    def test_policy_query_routes_tool_agent(self):
        self.graph._extra_order_id = lambda _: None
        self.graph._extra_invoice_info = lambda _: None

        state = {"messages": [HumanMessage(content="售后政策"), AIMessage(content="policy_query")]}
        route = self.graph._router_intent(state)
        self.assertEqual(route, "tool_agent")


if __name__ == "__main__":
    unittest.main()
