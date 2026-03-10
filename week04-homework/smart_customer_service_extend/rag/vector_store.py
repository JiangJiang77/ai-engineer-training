"""向量存储模块

使用ChromaDB进行向量存储和检索
"""
import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

from smart_customer_service_extend.config import settings
from smart_customer_service_extend.utils import get_logger

logger = get_logger(__name__)


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(
        self,
        persist_directory: str = "data/chroma_db",
        collection_name: str = "customer_service_kb"
    ):
        """初始化向量存储管理器
        
        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embeddings = None
        self.vectorstore = None
        
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        logger.debug(f"向量存储管理器初始化: persist_dir={persist_directory}, collection={collection_name}")
    
    def _get_embeddings(self):
        """获取embedding模型"""
        if self.embeddings is None:
            logger.debug("初始化DashScope Embedding模型")
            self.embeddings = DashScopeEmbeddings(
                model="text-embedding-v1",
                dashscope_api_key=settings.DASHSCOPE_API_KEY
            )
        return self.embeddings
    
    def create_vectorstore(self, documents: List[Document]) -> None:
        """创建向量存储
        
        Args:
            documents: 文档列表
        """
        logger.debug(f"开始创建向量存储,文档数量: {len(documents)}")
        
        embeddings = self._get_embeddings()
        
        # 创建向量存储
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory
        )
        
        logger.debug(f"✓ 向量存储创建成功,已持久化到: {self.persist_directory}")
    
    def load_vectorstore(self) -> bool:
        """加载已存在的向量存储
        
        Returns:
            是否加载成功
        """
        try:
            logger.debug(f"尝试加载向量存储: {self.persist_directory}")
            
            embeddings = self._get_embeddings()
            
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=embeddings,
                persist_directory=self.persist_directory
            )
            
            # 验证向量存储是否有数据
            collection = self.vectorstore._collection
            count = collection.count()
            
            if count == 0:
                logger.warning("向量存储为空")
                return False
            
            logger.debug(f"✓ 向量存储加载成功,包含 {count} 个向量")
            return True
        
        except Exception as e:
            logger.warning(f"加载向量存储失败: {e}")
            return False
    
    def similarity_search(
        self,
        query: str,
        k: int = 3,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件
        
        Returns:
            相关文档列表
        """
        if self.vectorstore is None:
            logger.error("向量存储未初始化")
            return []
        
        logger.debug(f"执行相似度搜索: query='{query}', k={k}")
        
        try:
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.debug(f"✓ 检索到 {len(results)} 个相关文档")
            
            # 记录检索结果
            for i, doc in enumerate(results):
                logger.debug(f"结果 {i+1}: source={doc.metadata.get('source')}, "
                           f"content_preview={doc.page_content[:50]}...")
            
            return results
        
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}", exc_info=True)
            return []
    
    def get_or_create_vectorstore(self, documents: Optional[List[Document]] = None) -> bool:
        """获取或创建向量存储
        
        Args:
            documents: 如果需要创建,使用的文档列表
        
        Returns:
            是否成功
        """
        # 尝试加载已存在的向量存储
        if self.load_vectorstore():
            return True
        
        # 如果加载失败且提供了文档,则创建新的向量存储
        if documents:
            logger.debug("向量存储不存在,开始创建新的向量存储")
            self.create_vectorstore(documents)
            return True
        
        logger.error("向量存储不存在且未提供文档")
        return False
