"""RAG模块测试

测试文档加载、向量存储和检索功能
"""
import unittest
import os
import shutil
from smart_customer_service.rag import load_documents, VectorStoreManager


class TestRAGModule(unittest.TestCase):
    """RAG模块测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试前准备"""
        # 确保在项目根目录
        cls.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(cls.project_root)
        
        # 清理测试向量数据库
        cls.test_db_path = "data/test_chroma_db"
        if os.path.exists(cls.test_db_path):
            shutil.rmtree(cls.test_db_path)
    
    @classmethod
    def tearDownClass(cls):
        """测试后清理"""
        # 清理测试向量数据库
        if os.path.exists(cls.test_db_path):
            shutil.rmtree(cls.test_db_path)
    
    def test_01_load_documents(self):
        """测试文档加载"""
        print("\n测试1: 文档加载")
        
        documents = load_documents(
            policy_path="policy.md",
            qa_path="QA.md",
            chunk_size=500,
            chunk_overlap=50
        )
        
        self.assertIsNotNone(documents)
        self.assertGreater(len(documents), 0)
        print(f"✓ 成功加载 {len(documents)} 个文档分块")
        
        # 检查文档元数据
        for doc in documents[:3]:
            self.assertIn("source", doc.metadata)
            self.assertIn("type", doc.metadata)
            print(f"  - 文档类型: {doc.metadata.get('type')}, 内容预览: {doc.page_content[:50]}...")
    
    def test_02_create_vectorstore(self):
        """测试向量存储创建"""
        print("\n测试2: 向量存储创建")
        
        # 加载文档
        documents = load_documents()
        self.assertGreater(len(documents), 0)
        
        # 创建向量存储
        manager = VectorStoreManager(
            persist_directory=self.test_db_path,
            collection_name="test_collection"
        )
        
        manager.create_vectorstore(documents)
        
        self.assertIsNotNone(manager.vectorstore)
        print(f"✓ 向量存储创建成功")
    
    def test_03_similarity_search(self):
        """测试相似度搜索"""
        print("\n测试3: 相似度搜索")
        
        # 加载文档并创建向量存储
        documents = load_documents()
        manager = VectorStoreManager(
            persist_directory=self.test_db_path,
            collection_name="test_collection"
        )
        manager.create_vectorstore(documents)
        
        # 测试查询
        test_queries = [
            "退货流程是什么?",
            "发货时效是多久?",
            "支持哪些支付方式?"
        ]
        
        for query in test_queries:
            print(f"\n  查询: {query}")
            results = manager.similarity_search(query, k=2)
            
            self.assertIsNotNone(results)
            self.assertGreater(len(results), 0)
            
            for i, doc in enumerate(results):
                print(f"    结果 {i+1}: {doc.metadata.get('type')} - {doc.page_content[:80]}...")
    
    def test_04_load_existing_vectorstore(self):
        """测试加载已存在的向量存储"""
        print("\n测试4: 加载已存在的向量存储")
        
        # 先创建向量存储
        documents = load_documents()
        manager1 = VectorStoreManager(
            persist_directory=self.test_db_path,
            collection_name="test_collection"
        )
        manager1.create_vectorstore(documents)
        
        # 创建新的管理器并加载
        manager2 = VectorStoreManager(
            persist_directory=self.test_db_path,
            collection_name="test_collection"
        )
        
        success = manager2.load_vectorstore()
        self.assertTrue(success)
        print(f"✓ 成功加载已存在的向量存储")
        
        # 测试搜索功能
        results = manager2.similarity_search("退款政策", k=1)
        self.assertGreater(len(results), 0)
        print(f"✓ 加载的向量存储可以正常搜索")


if __name__ == "__main__":
    unittest.main(verbosity=2)
