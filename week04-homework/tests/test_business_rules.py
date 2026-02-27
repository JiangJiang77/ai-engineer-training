"""测试订单去重和业务规则"""
import unittest
from datetime import datetime, timedelta
from smart_customer_service.database import (
    query_orders, get_user_by_username, create_order
)
from smart_customer_service.tools import (
    query_invoiceable_orders,
    query_refundable_orders
)


class TestOrderDeduplication(unittest.TestCase):
    """测试订单去重"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_user = get_user_by_username("test_user")
    
    def test_no_duplicate_orders(self):
        """测试订单无重复"""
        orders = query_orders(self.test_user["user_id"])
        order_ids = [o["order_id"] for o in orders]
        
        # 验证没有重复的订单ID
        self.assertEqual(
            len(order_ids),
            len(set(order_ids)),
            "订单ID不应该重复"
        )
    
    def test_unique_order_names_by_date(self):
        """测试同一天同名订单应该是不同订单"""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        orders = query_orders(self.test_user["user_id"], order_date=yesterday)
        
        # 统计每个订单名称的数量
        from collections import Counter
        name_counts = Counter([o["order_name"] for o in orders])
        
        # 如果有同名订单,它们的ID应该不同
        for name, count in name_counts.items():
            if count > 1:
                same_name_orders = [o for o in orders if o["order_name"] == name]
                order_ids = [o["order_id"] for o in same_name_orders]
                self.assertEqual(
                    len(order_ids),
                    len(set(order_ids)),
                    f"同名订单'{name}'的ID应该不同"
                )


class TestInvoiceBusinessRules(unittest.TestCase):
    """测试开票业务规则"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_user = get_user_by_username("test_user")
    
    def test_only_delivered_orders_can_invoice(self):
        """测试只有已签收订单可开票"""
        # 查询可开票订单(使用工具)
        result = query_invoiceable_orders.invoke({
            "user_id": self.test_user["user_id"]
        })
        
        # 如果有订单,验证都是已签收状态
        if "order_id" in result:
            import ast
            orders = ast.literal_eval(result)
            for order in orders:
                self.assertEqual(
                    order["status"],
                    "delivered",
                    "可开票订单必须是已签收状态"
                )
    
    def test_pending_orders_cannot_invoice(self):
        """测试待处理订单不可开票"""
        # 直接查询待处理且标记可开票的订单
        orders = query_orders(
            self.test_user["user_id"],
            status="pending",
            can_invoice=1
        )
        
        # 使用工具查询可开票订单
        result = query_invoiceable_orders.invoke({
            "user_id": self.test_user["user_id"]
        })
        
        # 工具返回的结果中不应该包含待处理订单
        if orders and "order_id" in result:
            import ast
            invoiceable_orders = ast.literal_eval(result)
            invoiceable_ids = [o["order_id"] for o in invoiceable_orders]
            
            for pending_order in orders:
                self.assertNotIn(
                    pending_order["order_id"],
                    invoiceable_ids,
                    "待处理订单不应该出现在可开票订单列表中"
                )
    
    def test_shipped_orders_cannot_invoice(self):
        """测试已发货订单不可开票"""
        # 查询已发货且标记可开票的订单
        orders = query_orders(
            self.test_user["user_id"],
            status="shipped",
            can_invoice=1
        )
        
        # 使用工具查询可开票订单
        result = query_invoiceable_orders.invoke({
            "user_id": self.test_user["user_id"]
        })
        
        # 工具返回的结果中不应该包含已发货订单
        if orders and "order_id" in result:
            import ast
            invoiceable_orders = ast.literal_eval(result)
            invoiceable_ids = [o["order_id"] for o in invoiceable_orders]
            
            for shipped_order in orders:
                self.assertNotIn(
                    shipped_order["order_id"],
                    invoiceable_ids,
                    "已发货订单不应该出现在可开票订单列表中"
                )


class TestRefundBusinessRules(unittest.TestCase):
    """测试退款业务规则"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        cls.test_user = get_user_by_username("test_user")
    
    def test_delivered_orders_cannot_refund(self):
        """测试已签收订单不可退款"""
        # 查询已签收的订单
        delivered_orders = query_orders(
            self.test_user["user_id"],
            status="delivered"
        )
        
        # 验证已签收订单的can_refund应该为0
        for order in delivered_orders:
            self.assertEqual(
                order["can_refund"],
                0,
                "已签收订单不应该可退款"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
