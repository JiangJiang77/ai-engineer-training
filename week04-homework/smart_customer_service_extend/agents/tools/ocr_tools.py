"""OCR相关工具"""
from langchain_core.tools import tool
from smart_customer_service_extend.utils import get_logger

logger = get_logger(__name__)


@tool
def extract_order_from_image_tool(image_path: str) -> str:
    """从订单图片中提取订单信息。输入: 图片相对路径(例如: 'images/order.png')。输出: 识别到的订单信息或提示。"""
    try:
        from smart_customer_service_extend.utils import extract_order_info_from_image

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


def create_ocr_tools() -> list:
    """创建OCR相关工具列表"""
    tools = [extract_order_from_image_tool]
    logger.debug(f"创建了 {len(tools)} 个OCR工具: {[t.name for t in tools]}")
    return tools
