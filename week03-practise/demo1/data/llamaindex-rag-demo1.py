# # 基础安装（Python 3.8+）  
# pip install llama-index langchain llama-cpp-python chromadb  

# # 扩展组件（按需安装）  
# pip install llama-index-embeddings-huggingface  # 本地嵌入模型支持  
# pip install docx2txt pdf2image           

import llama_index  

from llama_index.core import SimpleDirectoryReader  
from llama_index.core.node_parser import SemanticSplitterNodeParser  
from llama_index.embeddings.huggingface import HuggingFaceEmbedding  
from llama_index.core import VectorStoreIndex, StorageContext  
from llama_index.core import VectorStoreIndex, KeywordTableIndex  
from llama_index.core import SimpleDirectoryReader  
from llama_index.core.retrievers import QueryFusionRetriever  
from llama_index.core import load_index_from_storage  
from llama_index.llms.ollama import Ollama  

print(llama_index.__version__)  # 应≥0.10.0


# 三、数据加载与处理
# 3.1 多格式文档加载
# 使用SimpleDirectoryReader实现批量导入,加载本地文件夹：
# 支持格式：
# • 文本类：TXT/Markdown/HTML
# • 办公文档：PDF（需PyMuPDF）/Word/PPT
# • 代码文件：Python/Java/C++
documents = SimpleDirectoryReader(  
    input_dir="data",  
    required_exts=[".pdf", ".docx"],  
    recursive=True  
).load_data()  
print(f"已加载 {len(documents)} 份文档")


# 3.2 文本分块优化
# 配置语义分块策略：
# 分块参数：
# • chunk_size：建议512-1024 tokens
# • chunk_overlap：10%-20%防止语义断裂

embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")  
splitter = SemanticSplitterNodeParser(  
    embed_model=embed_model,  
    buffer_size=1,  
    breakpoint_percentile_threshold=95  
)  
nodes = splitter.get_nodes_from_documents(documents)


# 四、索引构建与持久化
# 4.1 向量索引创建
# 基于Hugging Face嵌入模型构建：

# 配置本地嵌入模型  
embed_model = HuggingFaceEmbedding(model_name="./models/bge-small-zh")  

# 构建索引  
# 索引类型选择： • 轻量级：ChromaDB（适合开发测试） • 高性能：FAISS（支持GPU加速） • 企业级：Weaviate（分布式扩展）
index = VectorStoreIndex(  
    nodes=nodes,  
    embed_model=embed_model,  
    show_progress=True  
)  
# 持久化存储  
index.storage_context.persist(persist_dir="index_storage")

# 4.2 混合索引策略
# 结合关键词与向量检索提升召回率：
# 创建双索引  
vector_index = VectorStoreIndex(nodes)  
keyword_index = KeywordTableIndex(nodes)  

# 组合检索器  
retriever = QueryFusionRetriever(  
    [vector_index.as_retriever(), keyword_index.as_retriever()],  
    similarity_top_k=5,  
    num_queries=3  
)
# 五、查询引擎与结果生成
# 5.1 基础查询实现


# 加载持久化索引  
storage_context = StorageContext.from_defaults(persist_dir="index_storage")  
index = load_index_from_storage(storage_context)  

# 创建查询引擎  
query_engine = index.as_query_engine(  
    similarity_top_k=3,  
    response_mode="compact"  
)  

# 执行查询  
response = query_engine.query("如何配置服务器安全策略？")  
print(response)
# 关键参数：
# • similarity_top_k：检索结果数量（平衡精度与速度）
# • response_mode：compact（简洁）/refine（迭代优化）

# 5.2 本地模型集成
# 使用Ollama运行DeepSeek等本地模型：

# 初始化本地模型  
llm = Ollama(model="deepseek-r1:7b", temperature=0.3)  

# 注入自定义模型  
query_engine = index.as_query_engine(llm=llm)
# 模型选择建议：
# • 通用场景：DeepSeek-R1-7B
# • 专业领域：CodeLlama-34B
# • 轻量化部署：Phi-3-mini