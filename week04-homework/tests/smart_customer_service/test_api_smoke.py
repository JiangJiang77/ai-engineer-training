import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.smart_customer_service._stub_reportlab import install_reportlab_stub

install_reportlab_stub()

from smart_customer_service import api as api_module


class TestLanggraphDemoAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api_module.app)

    def test_chat_returns_response(self):
        with patch.object(api_module.graph_manager, "invoke_workflow", return_value="ok"):
            resp = self.client.post(
                "/chat",
                json={"user_id": "u1", "content": "你好"},
            )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["user_id"], "u1")
        self.assertEqual(body["response"], "ok")

    def test_hot_update_invalid_type_returns_error(self):
        resp = self.client.post(
            "/hot_update",
            json={"tool_type": "invalid_tool", "model_name": "qwen-plus"},
        )
        # 当前实现会统一包装成 500
        self.assertEqual(resp.status_code, 500)
        self.assertIn("热更新失败", resp.json().get("detail", ""))


if __name__ == "__main__":
    unittest.main()
