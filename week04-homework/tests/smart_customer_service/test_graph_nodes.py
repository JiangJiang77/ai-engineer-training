import unittest

from langchain_core.messages import AIMessage, HumanMessage

from tests.smart_customer_service._stub_reportlab import install_reportlab_stub

install_reportlab_stub()

from smart_customer_service.graph import GraphManager


class TestGraphNodes(unittest.TestCase):
    def setUp(self):
        self.graph = object.__new__(GraphManager)

    def test_ask_order_id_node(self):
        result = self.graph._ask_order_id({"messages": []})
        self.assertEqual(result["messages"][0].content, "请提供订单号")

    def test_ask_invoice_info_node(self):
        result = self.graph._ask_invoice_info({"messages": []})
        self.assertEqual(result["messages"][0].content, "请提供发票信息(订单号、姓名、税号)")

    def test_should_continue_with_tool_calls(self):
        ai = AIMessage(
            content="",
            tool_calls=[{"name": "get_order_detail", "args": {"order_id": "1"}, "id": "t1", "type": "tool_call"}],
        )
        route = self.graph._should_continue({"messages": [ai]})
        self.assertEqual(route, "tools")

    def test_should_continue_without_tool_calls(self):
        ai = AIMessage(content="普通回复")
        route = self.graph._should_continue({"messages": [ai]})
        self.assertEqual(route, "chat_bot")

    def test_get_latest_user_input(self):
        state = {
            "messages": [
                HumanMessage(content="第一条"),
                AIMessage(content="中间回复"),
                HumanMessage(content="最后一条用户输入"),
            ]
        }
        latest = self.graph._get_latest_user_input(state)
        self.assertEqual(latest, "最后一条用户输入")


if __name__ == "__main__":
    unittest.main()
