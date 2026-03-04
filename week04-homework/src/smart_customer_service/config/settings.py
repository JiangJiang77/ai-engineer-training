"""配置管理模块

从环境变量和配置文件加载系统配置
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    """系统配置类"""
    
    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent.parent
    
    # LLM配置
    DASHSCOPE_API_KEY_NAME: str = os.getenv("DASHSCOPE_API_KEY_NAME", "")
    DASHSCOPE_API_KEY: str = os.getenv(DASHSCOPE_API_KEY_NAME, "")
    LLM_MODEL: str = "qwen-turbo"
    LLM_TEMPERATURE: float = 0.7
    
    # Agent模式配置
    AGENT_MODE: str = os.getenv("AGENT_MODE", "react")  # react 或 workflow
    USE_REACT_AGENT: bool = True  # 是否启用ReAct Agent
    REACT_MAX_ITERATIONS: int = 5  # 最大迭代次数
    REACT_VERBOSE: bool = True  # 是否显示推理过程

    
    # 数据库配置
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/customer_service.db")
    
    # 阿里云ASR配置
    ALIYUN_ACCESS_KEY_ID: str = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    ALIYUN_ASR_APP_KEY: str = os.getenv("ALIYUN_ASR_APP_KEY", "")
    
    # 阿里云OCR配置
    ALIYUN_OCR_ACCESS_KEY_ID: str = os.getenv("ALIYUN_OCR_ACCESS_KEY_ID", "")
    ALIYUN_OCR_ACCESS_KEY_SECRET: str = os.getenv("ALIYUN_OCR_ACCESS_KEY_SECRET", "")
    
    # LangSmith配置(可选)
    LANGSMITH_API_KEY: Optional[str] = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "customer-service-system")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库URL"""
        db_path = Path(cls.DATABASE_PATH)
        if not db_path.is_absolute():
            db_path = cls.BASE_DIR / db_path
        return f"sqlite:///{db_path}"
    
    @classmethod
    def validate(cls) -> bool:
        """验证必要的配置是否存在"""
        if not cls.DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY is required")
        return True


# 全局配置实例
settings = Settings()
