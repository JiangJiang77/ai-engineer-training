"""OCR订单识别模块

使用阿里云Qwen-VL-Max多模态模型识别订单图片并提取订单信息
"""
import base64
import json
from pathlib import Path
from typing import Dict, Optional

from smart_customer_service_extend.config import settings
from smart_customer_service_extend.utils import get_logger

logger = get_logger(__name__)


def extract_order_info_from_image(image_path: str) -> Dict:
    """从订单图片中提取订单信息
    
    Args:
        image_path: 图片路径(支持相对路径和绝对路径)
        
    Returns:
        订单信息字典,包含:
        - order_id: 订单号
        - order_name: 商品名称
        - price: 价格
        - status: 订单状态
        - logistics_status: 物流状态
        - shop_name: 店铺名称
        - receiver_info: 收货人信息
        - error: 错误信息(如果识别失败)
        
    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 图片格式不支持
    """
    try:
        # 转换为绝对路径
        img_path = Path(image_path)
        if not img_path.is_absolute():
            # 相对路径基于项目根目录
            img_path = settings.BASE_DIR / image_path
        
        # 验证文件存在
        if not img_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {img_path}")
        
        # 验证文件格式
        supported_formats = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        if img_path.suffix.lower() not in supported_formats:
            raise ValueError(f"不支持的图片格式: {img_path.suffix}. 支持的格式: {supported_formats}")
        
        logger.info(f"开始识别订单图片: {img_path}")
        
        # 读取图片并转换为base64
        with open(img_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # 调用Qwen-VL-Max模型
        result = _call_qwen_vl_max(image_data)
        
        logger.info(f"订单信息识别成功: {result.get('order_id', 'N/A')}")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        return {"error": str(e)}
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"OCR识别失败: {e}", exc_info=True)
        return {"error": f"识别失败: {str(e)}"}


def _call_qwen_vl_max(image_base64: str) -> Dict:
    """调用Qwen-VL-Max模型识别订单图片
    
    Args:
        image_base64: base64编码的图片数据
        
    Returns:
        订单信息字典
    """
    import dashscope
    from dashscope import MultiModalConversation
    
    # 设置API Key
    dashscope.api_key = settings.DASHSCOPE_API_KEY
    
    # 构造提示词
    prompt = """请仔细分析这张订单截图,提取以下订单信息:

1. 订单号(order_id): 完整的订单编号
2. 商品名称(order_name): 商品的完整名称和规格
3. 价格(price): 实付款金额(数字,不带货币符号)
4. 订单状态(status): 如"已签收"、"运输中"、"待发货"等
5. 物流状态(logistics_status): 详细的物流信息,包括配送地址、收货人等
6. 店铺名称(shop_name): 商家店铺名称
7. 收货人信息(receiver_info): 收货人姓名和电话(如果有)

请以JSON格式返回,格式如下:
{
    "order_id": "订单号",
    "order_name": "商品名称",
    "price": "价格",
    "status": "订单状态",
    "logistics_status": "物流状态",
    "shop_name": "店铺名称",
    "receiver_info": "收货人信息"
}

如果某些信息在图片中不存在,请填写"未知"。
"""
    
    # 构造消息
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"data:image/jpeg;base64,{image_base64}"},
                {"text": prompt}
            ]
        }
    ]
    
    try:
        # 调用API
        logger.debug("调用Qwen-VL-Max API...")
        response = MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        # 解析响应
        if response.status_code == 200:
            output_text = response.output.choices[0].message.content[0]['text']
            logger.debug(f"API响应: {output_text}")
            
            # 尝试解析JSON
            try:
                # 提取JSON部分(可能包含在markdown代码块中)
                if '```json' in output_text:
                    json_str = output_text.split('```json')[1].split('```')[0].strip()
                elif '```' in output_text:
                    json_str = output_text.split('```')[1].split('```')[0].strip()
                else:
                    json_str = output_text.strip()
                
                order_info = json.loads(json_str)
                return order_info
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败,返回原始文本: {e}")
                return {
                    "error": "JSON解析失败",
                    "raw_response": output_text
                }
        else:
            error_msg = f"API调用失败: {response.code} - {response.message}"
            logger.error(error_msg)
            return {"error": error_msg}
            
    except Exception as e:
        logger.error(f"调用Qwen-VL-Max API失败: {e}", exc_info=True)
        return {"error": f"API调用失败: {str(e)}"}
