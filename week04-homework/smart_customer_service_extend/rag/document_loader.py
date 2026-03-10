"""文档加载模块

加载政策文档和QA文档,并进行分块处理
"""
import os
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from smart_customer_service_extend.utils import get_logger

logger = get_logger(__name__)


def _resolve_doc_path(doc_path: str) -> Optional[str]:
    """解析文档路径.

    优先级:
    1) 传入绝对路径
    2) 当前工作目录
    3) 项目根目录(week04-homework)
    """
    path = Path(doc_path)
    if path.is_absolute() and path.exists():
        return str(path)

    cwd_candidate = Path.cwd() / doc_path
    if cwd_candidate.exists():
        return str(cwd_candidate)

    project_root = Path(__file__).resolve().parents[2]
    root_candidate = project_root / doc_path
    if root_candidate.exists():
        return str(root_candidate)

    return None


def load_documents(
    policy_path: str = "policy.md",
    qa_path: str = "QA.md",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """加载并分块文档
    
    Args:
        policy_path: 政策文档路径
        qa_path: QA文档路径
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小
    
    Returns:
        分块后的文档列表
    """
    documents = []
    
    resolved_policy_path = _resolve_doc_path(policy_path)
    resolved_qa_path = _resolve_doc_path(qa_path)

    # 加载 policy.md
    if resolved_policy_path:
        logger.debug(f"加载政策文档: {resolved_policy_path}")
        loader = TextLoader(resolved_policy_path, encoding="utf-8")
        policy_docs = loader.load()
        
        # 为文档添加元数据
        for doc in policy_docs:
            doc.metadata["source"] = "policy"
            doc.metadata["type"] = "政策文档"
        
        documents.extend(policy_docs)
        logger.debug(f"✓ 加载政策文档成功,共 {len(policy_docs)} 个文档")
    else:
        logger.warning(f"政策文档不存在: {policy_path}")
    
    # 加载 QA.md
    if resolved_qa_path:
        logger.debug(f"加载QA文档: {resolved_qa_path}")
        loader = TextLoader(resolved_qa_path, encoding="utf-8")
        qa_docs = loader.load()
        
        # 为文档添加元数据
        for doc in qa_docs:
            doc.metadata["source"] = "qa"
            doc.metadata["type"] = "QA知识库"
        
        documents.extend(qa_docs)
        logger.debug(f"✓ 加载QA文档成功,共 {len(qa_docs)} 个文档")
    else:
        logger.warning(f"QA文档不存在: {qa_path}")
    
    if not documents:
        logger.error("没有加载到任何文档")
        return []
    
    # 文档分块
    logger.debug(f"开始文档分块: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    )
    
    split_docs = text_splitter.split_documents(documents)
    logger.debug(f"✓ 文档分块完成,共 {len(split_docs)} 个分块")
    
    return split_docs
