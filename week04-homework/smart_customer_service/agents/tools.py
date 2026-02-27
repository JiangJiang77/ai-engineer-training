"""ReAct Agent工具定义

将现有业务功能封装为工具函数,供Agent调用
"""
from langchain_core.tools import tool
from smart_customer_service.utils import get_logger

logger = get_logger(__name__)


def create_customer_service_tools(user_id: str) -> list:
    """创建客服工具列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        工具列表
    """
    
    # 工具1: 查询订单
    @tool
    def query_orders_tool(params_str: str) -> str:
        """查询用户订单。输入格式: keyword=商品名,date=时间 (两个参数都是可选的,也可以为空查询所有订单)。示例: keyword=笔记本,date=昨天 或 date=昨天 或 keyword=笔记本 或 空字符串"""
        try:
            from smart_customer_service.database import query_orders
            from smart_customer_service.utils import parse_relative_time
            
            # 解析参数
            params = {}
            if params_str.strip():
                for item in params_str.split(','):
                    if '=' in item:
                        k, v = item.split('=', 1)
                        params[k.strip()] = v.strip()
            
            filters = {}
            if 'keyword' in params:
                filters['keyword'] = params['keyword']
            if 'date' in params:
                try:
                    date_obj = parse_relative_time(params['date'])
                    filters['order_date'] = date_obj.date()
                except Exception as e:
                    logger.warning(f"日期解析失败: {params['date']}, 错误: {e}")
            
            logger.debug(f"[Tool] QueryOrders: user_id={user_id}, filters={filters}")
            
            orders = query_orders(user_id, filters=filters)

            
            if not orders:
                return "未找到符合条件的订单"
            
            # 格式化输出
            result = []
            for order in orders:
                order_date = order['order_date']
                if hasattr(order_date, 'strftime'):
                    order_date = order_date.strftime("%Y-%m-%d")
                
                result.append(
                    f"订单号:{order['order_id']}, "
                    f"商品:{order['order_name']}, "
                    f"金额:{order.get('amount', 0)}元, "
                    f"状态:{order['status']}, "
                    f"日期:{order_date}"
                )
            
            return "\n".join(result)
            
        except Exception as e:
            logger.error(f"[Tool Error] QueryOrders: {e}", exc_info=True)
            return f"查询订单失败: {str(e)}"
    
    # 工具2: 获取物流信息
    @tool
    def get_logistics_tool(order_id: str) -> str:
        """获取订单物流信息。输入: 订单号(完整的UUID格式)。示例: 33ca60d5-3d02-4df1-97f6-daba79a7e294"""
        try:
            from smart_customer_service.database.crud import get_db_session
            from smart_customer_service.database.models import Order
            
            order_id = order_id.strip()
            logger.debug(f"[Tool] GetLogistics: order_id={order_id}")
            
            with get_db_session() as session:
                order = session.query(Order).filter(Order.order_id == order_id).first()
                
                if not order:
                    return f"未找到订单 {order_id}"
                
                return (
                    f"订单【{order.order_name}】\n"
                    f"物流状态: {order.logistics_status}\n"
                    f"订单状态: {order.status}"
                )
                
        except Exception as e:
            logger.error(f"[Tool Error] GetLogistics: {e}", exc_info=True)
            return f"获取物流信息失败: {str(e)}"
    
    # 工具3: 提交退款
    @tool
    def submit_refund_tool(order_id: str) -> str:
        """提交退款申请。输入: 订单号(完整的UUID格式)。注意: 只有可退款的订单才能提交退款"""
        try:
            from smart_customer_service.database import update_order_status
            from smart_customer_service.database.crud import get_db_session
            from smart_customer_service.database.models import Order
            
            order_id = order_id.strip()
            logger.debug(f"[Tool] SubmitRefund: order_id={order_id}")
            
            # 先检查订单是否可退款
            with get_db_session() as session:
                order = session.query(Order).filter(Order.order_id == order_id).first()
                
                if not order:
                    return f"未找到订单 {order_id}"
                
                if order.can_refund == 0:
                    return f"订单【{order.order_name}】不支持退款"
            
            # 更新状态
            order = update_order_status(order_id, "refunding")
            return f"订单【{order.order_name}】退款申请已提交,预计3-5个工作日退款到账"
            
        except Exception as e:
            logger.error(f"[Tool Error] SubmitRefund: {e}", exc_info=True)
            return f"提交退款失败: {str(e)}"
    
    # 工具4: 开具发票
    @tool
    def issue_invoice_tool(order_id: str) -> str:
        """开具发票。输入: 订单号(完整的UUID格式)。注意: 只有已签收的订单才能开具发票"""
        try:
            from smart_customer_service.database import get_order_by_id, update_order_invoice_status
            
            order_id = order_id.strip()
            logger.debug(f"[Tool] IssueInvoice: order_id={order_id}")
            
            order = get_order_by_id(order_id)
            
            if not order:
                return f"未找到订单 {order_id}"
            
            if order["can_invoice"] == 0:
                return f"订单【{order['order_name']}】不可开票(只有已签收订单才能开票)"
            
            if order.get("invoice_status") == "已开票":
                return f"订单【{order['order_name']}】已开具过发票,无需重复开具"
            
            update_order_invoice_status(order_id, "已开票")
            return f"订单【{order['order_name']}】发票已开具,将在3个工作日内寄出"
            
        except Exception as e:
            logger.error(f"[Tool Error] IssueInvoice: {e}", exc_info=True)
            return f"开具发票失败: {str(e)}"
    
    # 工具5: 搜索政策
    @tool
    def search_policy_tool(query: str) -> str:
        """搜索公司政策文档,包括退换货政策、物流政策、发票政策、质保政策等。输入: 查询关键词。示例: 退货政策 或 发票规则 或 保修期"""
        try:
            from smart_customer_service.rag import load_documents, VectorStoreManager
            
            query = query.strip()
            logger.debug(f"[Tool] SearchPolicy: query={query}")
            
            vector_store = VectorStoreManager()
            if not vector_store.load_vectorstore():
                documents = load_documents()
                if not documents:
                    return "政策文档加载失败"
                vector_store.create_vectorstore(documents)
            
            docs = vector_store.similarity_search(query, k=3)
            
            if not docs:
                return "未找到相关政策信息"
            
            result = "\n\n".join([
                f"【{doc.metadata.get('type', '文档')}】\n{doc.page_content}"
                for doc in docs
            ])
            
            return result
            
        except Exception as e:
            logger.error(f"[Tool Error] SearchPolicy: {e}", exc_info=True)
            return f"政策查询失败: {str(e)}"

    # 工具6: 图片提取订单信息
    @tool
    def extract_order_from_image_tool(image_path: str) -> str:
        """从订单图片中提取订单信息。输入: 图片的相对路径 (例如: 'images/order.png')。"""
        try:
            from smart_customer_service.utils import extract_order_info_from_image
            
            image_path = image_path.strip()
            logger.debug(f"[Tool] ExtractOrderFromImage: image_path={image_path}")
            
            result = extract_order_info_from_image(image_path)
            
            if "error" in result:
                return f"识别图片失败: {result['error']}"
            
            # 格式化识别结果
            info_list = []
            if result.get("order_id") and result["order_id"] != "未知":
                info_list.append(f"订单号: {result['order_id']}")
            if result.get("order_name") and result["order_name"] != "未知":
                info_list.append(f"商品名称: {result['order_name']}")
            if result.get("price") and result["price"] != "未知":
                info_list.append(f"价格: {result['price']}元")
            if result.get("status") and result["status"] != "未知":
                info_list.append(f"订单状态: {result['status']}")
            if result.get("logistics_status") and result["logistics_status"] != "未知":
                info_list.append(f"物流状态: {result['logistics_status']}")
            if result.get("shop_name") and result["shop_name"] != "未知":
                info_list.append(f"店铺名称: {result['shop_name']}")
            
            if not info_list:
                return "图片中未识别到有效的订单信息"
            
            return "\n".join(info_list)
            
        except Exception as e:
            logger.error(f"[Tool Error] ExtractOrderFromImage: {e}", exc_info=True)
            return f"识别图片出错: {str(e)}"
    
    # 返回工具列表
    tools = [
        query_orders_tool,
        get_logistics_tool,
        submit_refund_tool,
        issue_invoice_tool,
        search_policy_tool,
        extract_order_from_image_tool
    ]
    
    logger.debug(f"创建了 {len(tools)} 个工具: {[t.name for t in tools]}")
    
    return tools
