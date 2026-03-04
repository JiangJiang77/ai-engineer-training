"""多模态输入工具

提供语音识别和OCR功能(阿里云服务)
"""
from typing import Optional
from langchain.tools import tool

from smart_customer_service.config import settings
from smart_customer_service.utils import logger


@tool
def speech_to_text(audio_data: bytes) -> str:
    """语音转文本(阿里云ASR)
    
    Args:
        audio_data: 音频数据
    
    Returns:
        识别的文本
    """
    try:
        # TODO: 集成阿里云ASR SDK
        # 这里先返回模拟结果
        logger.warning("阿里云ASR功能尚未实现,返回模拟结果")
        return "查看我的订单"
    except Exception as e:
        logger.error(f"语音识别失败: {e}")
        return f"语音识别失败: {str(e)}"


@tool
def extract_order_number(image_data: bytes) -> str:
    """从图像中提取订单号(阿里云OCR)
    
    Args:
        image_data: 图像数据
    
    Returns:
        提取的订单号
    """
    try:
        # TODO: 集成阿里云OCR SDK
        # 这里先返回模拟结果
        logger.warning("阿里云OCR功能尚未实现,返回模拟结果")
        return "ORD20260211001"
    except Exception as e:
        logger.error(f"OCR识别失败: {e}")
        return f"OCR识别失败: {str(e)}"


def test_aliyun_connection():
    """测试阿里云服务连接"""
    print("🔍 测试阿里云服务连接...")
    
    # 检查配置
    if not settings.ALIYUN_ACCESS_KEY_ID:
        print("⚠️  未配置 ALIYUN_ACCESS_KEY_ID")
    else:
        print(f"✅ ALIYUN_ACCESS_KEY_ID: {settings.ALIYUN_ACCESS_KEY_ID[:10]}...")
    
    if not settings.ALIYUN_ASR_APP_KEY:
        print("⚠️  未配置 ALIYUN_ASR_APP_KEY")
    else:
        print(f"✅ ALIYUN_ASR_APP_KEY: {settings.ALIYUN_ASR_APP_KEY[:10]}...")
    
    print("💡 提示: 多模态功能需要配置阿里云AccessKey")
