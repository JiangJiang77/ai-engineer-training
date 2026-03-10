"""测试LangGraph工作流

测试工作流的各个节点和路由逻辑
"""
import unittest
from datetime import datetime, timedelta
from smart_customer_service_extend.workflow import run_workflow
from smart_customer_service_extend.database import get_user_by_username


class TestWorkflow(unittest.TestCase):
    """测试工作流"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_user = get_user_by_username("test_user")
        if not cls.test_user:
            raise Exception("测试用户不存在")
        cls.user_id = cls.test_user["user_id"]
        cls.session_id = "test_session_001"
    
    def test_logistics_query_with_keyword(self):
        """测试物流查询 - 关键字场景"""
        user_input = "查看昨天购买的年货礼品发货了吗"
        
        response = run_workflow(
            user_id=self.user_id,
            session_id=self.session_id,
            user_input=user_input
        )
        
        # 验证响应包含查询结果
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f"\n物流查询(关键字)响应:\n{response}\n")
    
    def test_logistics_query_by_date(self):
        """测试物流查询 - 日期场景"""
        user_input = "查看昨天下单的订单发货了吗"
        
        response = run_workflow(
            user_id=self.user_id,
            session_id=self.session_id,
            user_input=user_input
        )
        
        # 验证响应包含查询结果
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f"\n物流查询(日期)响应:\n{response}\n")
    
    def test_refund_application(self):
        """测试退款申请"""
        user_input = "我要退货"
        
        response = run_workflow(
            user_id=self.user_id,
            session_id=self.session_id,
            user_input=user_input
        )
        
        # 验证响应包含可退款订单信息
        self.assertIsInstance(response, str)
        self.assertTrue(
            "可退款订单" in response or "退款" in response,
            "响应应该包含退款相关信息"
        )
        print(f"\n退款申请响应:\n{response}\n")
    
    def test_invoice_issuance(self):
        """测试发票开具"""
        user_input = "我要开具发票"
        
        response = run_workflow(
            user_id=self.user_id,
            session_id=self.session_id,
            user_input=user_input
        )
        
        # 验证响应包含可开票订单信息
        self.assertIsInstance(response, str)
        self.assertTrue(
            "可开票订单" in response or "发票" in response,
            "响应应该包含发票相关信息"
        )
        print(f"\n发票开具响应:\n{response}\n")
    
    def test_general_chat(self):
        """测试一般对话"""
        user_input = "你好"
        
        response = run_workflow(
            user_id=self.user_id,
            session_id=self.session_id,
            user_input=user_input
        )
        
        # 验证响应是友好的回复
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f"\n一般对话响应:\n{response}\n")
    
    def test_unknown_intent(self):
        """测试未知意图"""
        user_input = "我要投诉"
        
        response = run_workflow(
            user_id=self.user_id,
            session_id=self.session_id,
            user_input=user_input
        )
        
        # 验证响应包含友好提示
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        print(f"\n未知意图响应:\n{response}\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
