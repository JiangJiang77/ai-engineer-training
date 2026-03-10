"""RAG检索模块

提供文档加载、向量存储和检索功能
"""
from smart_customer_service_extend.rag.document_loader import load_documents
from smart_customer_service_extend.rag.vector_store import VectorStoreManager

__all__ = ["load_documents", "VectorStoreManager"]
