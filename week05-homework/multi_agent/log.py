import logging


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.DEBUG),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("mcp").setLevel(logging.INFO)
    logging.getLogger("dashscope").setLevel(logging.INFO)



def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
