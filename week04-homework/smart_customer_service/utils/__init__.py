"""工具模块"""
import sys

from smart_customer_service.utils.time_parser import parse_relative_time
from smart_customer_service.utils.logger import setup_logger, get_logger, logger
from smart_customer_service.client import ocr as _ocr, asr as _asr

# 兼容旧导入路径: smart_customer_service.utils.ocr / asr
sys.modules.setdefault(__name__ + ".ocr", _ocr)
sys.modules.setdefault(__name__ + ".asr", _asr)

extract_order_info_from_image = _ocr.extract_order_info_from_image
speech_to_text = _asr.speech_to_text

__all__ = [
    "parse_relative_time",
    "setup_logger",
    "get_logger",
    "logger",
    "extract_order_info_from_image",
    "speech_to_text",
]
