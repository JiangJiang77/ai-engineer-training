import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mcp_research_url: str
    log_level: str
    default_topic: str
    base_thread_id: str
    checkpoint_db: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mcp_research_url=os.getenv("MCP_RESEARCH_URL", "http://127.0.0.1:8000/mcp"),
            log_level=os.getenv("LOG_LEVEL", "DEBUG").upper(),
            default_topic=os.getenv("DEFAULT_TOPIC", "CrewAI和Langgraph的实现原理和技术选型对比"),
            base_thread_id=os.getenv("BASE_THREAD_ID", "writer-thread-002"),
            checkpoint_db=os.getenv("CHECKPOINT_DB", "multi_agent/checkpoints/writer.sqlite"),
        )


SETTINGS = Settings.from_env()
