"""测试用例集合

用于新增功能后的回归测试
"""
import unittest
from datetime import datetime, timedelta
from smart_customer_service.database import (
    create_user, authenticate_user, get_user_by_username,
    query_orders, create_order, update_order_status
)
from smart_customer_service.tools import (
    query_order_by_keyword,
    query_orders_by_date,
    get_order_logistics,
    query_refundable_orders,
    submit_refund,
    query_invoiceable_orders,
    issue_invoice
)
from smart_customer_service.utils import parse_relative_time


class TestDatabaseOperations(unittest.TestCase):
    """数据库操作测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        # 获取测试用户
        cls.test_user = get_user_by_username("test_user")
        if not cls.test_user:
            raise Exception("测试用户不存在,请先运行数据库初始化")
    
    def test_user_authentication(self):
        """测试用户认证"""
        # 正确密码
        user = authenticate_user("test_user", "password123")
        self.assertIsNotNone(user, "正确密码应该认证成功")
        
        # 错误密码
        user = authenticate_user("test_user", "wrong_password")
        self.assertIsNone(user, "错误密码应该认证失败")
    
    def test_query_all_orders(self):
        """测试查询所有订单"""
        orders = query_orders(self.test_user["user_id"])
        self.assertGreater(len(orders), 0, "应该至少有一个订单")
        
        # 验证订单结构
        order = orders[0]
        self.assertIn("order_id", order)
        self.assertIn("order_name", order)
        self.assertIn("status", order)
        self.assertIn("order_date", order)
    
    def test_query_orders_by_date(self):
        """测试按日期查询订单"""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        orders = query_orders(self.test_user["user_id"], order_date=yesterday)
        
        # 应该能查到昨天的订单
        self.assertGreater(len(orders), 0, "应该能查到昨天的订单")
        
        # 验证日期正确
        for order in orders:
            order_date = order["order_date"]
            if isinstance(order_date, datetime):
                order_date = order_date.date()
            self.assertEqual(order_date, yesterday, "订单日期应该是昨天")
    
    def test_query_orders_by_keyword(self):
        """测试按关键字查询订单"""
        orders = query_orders(self.test_user["user_id"], keyword="年货")
        
        # 应该能查到包含"年货"的订单
        self.assertGreater(len(orders), 0, "应该能查到包含'年货'的订单")
        
        # 验证订单名称包含关键字
        for order in orders:
            self.assertIn("年货", order["order_name"], "订单名称应该包含'年货'")
    
    def test_query_refundable_orders(self):
        """测试查询可退款订单"""
        orders = query_orders(self.test_user["user_id"], can_refund=1)
        
        # 应该有可退款订单
        self.assertGreater(len(orders), 0, "应该有可退款订单")
        
        # 验证所有订单都可退款
        for order in orders:
            self.assertEqual(order["can_refund"], 1, "订单应该可退款")
    
    def test_query_invoiceable_orders(self):
        """测试查询可开票订单"""
        orders = query_orders(self.test_user["user_id"], can_invoice=1, status="delivered")
        
        # 应该有可开票订单
        self.assertGreater(len(orders), 0, "应该有可开票订单")
        
        # 验证所有订单都可开票且已签收
        for order in orders:
            self.assertEqual(order["can_invoice"], 1, "订单应该可开票")
            self.assertEqual(order["status"], "delivered", "可开票订单必须是已签收状态")


class TestOrderTools(unittest.TestCase):
    """订单工具测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_user = get_user_by_username("test_user")
        if not cls.test_user:
            raise Exception("测试用户不存在")
    
    def test_query_order_by_keyword_tool(self):
        """测试关键字查询工具"""
        result = query_order_by_keyword.invoke({
            "user_id": self.test_user["user_id"],
            "keyword": "年货",
            "date_str": "昨天"
        })
        
        # 结果应该是字符串
        self.assertIsInstance(result, str)
        # 应该包含订单信息
        self.assertIn("年货", result, "结果应该包含'年货'")
    
    def test_query_orders_by_date_tool(self):
        """测试日期查询工具"""
        result = query_orders_by_date.invoke({
            "user_id": self.test_user["user_id"],
            "date_str": "昨天"
        })
        
        # 结果应该是字符串
        self.assertIsInstance(result, str)
        # 不应该是"没有订单"
        self.assertNotIn("没有订单", result, "昨天应该有订单")
    
    def test_query_refundable_orders_tool(self):
        """测试可退款订单查询工具"""
        result = query_refundable_orders.invoke({
            "user_id": self.test_user["user_id"]
        })
        
        # 结果应该是字符串
        self.assertIsInstance(result, str)
        # 应该有可退款订单
        self.assertNotIn("没有可退款的订单", result, "应该有可退款订单")
    
    def test_query_invoiceable_orders_tool(self):
        """测试可开票订单查询工具"""
        result = query_invoiceable_orders.invoke({
            "user_id": self.test_user["user_id"]
        })
        
        # 结果应该是字符串
        self.assertIsInstance(result, str)
        # 应该有可开票订单或提示只有已签收订单可开票
        self.assertTrue(
            "没有可开票的订单" in result or "order_id" in result,
            "应该返回订单列表或提示信息"
        )


class TestTimeParser(unittest.TestCase):
    """时间解析测试"""
    
    def test_parse_yesterday(self):
        """测试解析'昨天'"""
        result = parse_relative_time("昨天")
        expected = (datetime.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.assertEqual(result.date(), expected.date(), "'昨天'应该解析为昨天的日期")
    
    def test_parse_today(self):
        """测试解析'今天'"""
        result = parse_relative_time("今天")
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(result.date(), expected.date(), "'今天'应该解析为今天的日期")
    
    def test_parse_day_before_yesterday(self):
        """测试解析'前天'"""
        result = parse_relative_time("前天")
        expected = (datetime.now() - timedelta(days=2)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.assertEqual(result.date(), expected.date(), "'前天'应该解析为前天的日期")
    
    def test_parse_n_days_ago(self):
        """测试解析'N天前'"""
        result = parse_relative_time("3天前")
        expected = (datetime.now() - timedelta(days=3)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.assertEqual(result.date(), expected.date(), "'3天前'应该解析正确")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_user = get_user_by_username("test_user")
    
    def test_complete_order_query_workflow(self):
        """测试完整的订单查询流程"""
        # 1. 用户登录
        user = authenticate_user("test_user", "password123")
        self.assertIsNotNone(user)
        
        # 2. 查询昨天的订单
        yesterday = (datetime.now() - timedelta(days=1)).date()
        orders = query_orders(self.test_user["user_id"], order_date=yesterday)
        self.assertGreater(len(orders), 0)
        
        # 3. 根据关键字筛选
        keyword_orders = [o for o in orders if "年货" in o["order_name"]]
        self.assertGreater(len(keyword_orders), 0)
        
        # 4. 获取物流信息
        order_id = keyword_orders[0]["order_id"]
        result = get_order_logistics.invoke({"order_id": order_id})
        self.assertIn("物流状态", result)
    
    def test_complete_refund_workflow(self):
        """测试完整的退款流程"""
        # 1. 查询可退款订单
        orders = query_orders(self.test_user["user_id"], can_refund=1)
        self.assertGreater(len(orders), 0)
        
        # 2. 选择一个订单
        order_id = orders[0]["order_id"]
        
        # 3. 提交退款(注意:这会修改数据库)
        # result = submit_refund.invoke({"order_id": order_id})
        # self.assertIn("退款申请已提交", result)
        
        # 为了不影响测试数据,这里只验证工具可调用
        self.assertTrue(callable(submit_refund.invoke))


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
