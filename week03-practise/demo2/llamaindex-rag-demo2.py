import os
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.dashscope import DashScopeEmbedding, DashScopeTextEmbeddingModels
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

api_key = os.getenv("DASHSCOPE_API_KEY")
print(f"DASHSCOPE_API_KEY: {api_key}")


# 1️⃣ Load｜加载数据 → Document
# Load：从目录中加载文档
documents = SimpleDirectoryReader(
    input_dir="./docs"
).load_data()

print(f"Loaded {len(documents)} documents")

# 2️⃣ Split｜Document → Node
# Split：定义切分策略
splitter = SentenceSplitter(
    chunk_size=512,
    chunk_overlap=100
)

nodes = splitter.get_nodes_from_documents(documents)
print(f"Split into {len(nodes)} nodes")


embed_model = DashScopeEmbedding(
        model_name=DashScopeTextEmbeddingModels.TEXT_EMBEDDING_V3,
        embed_batch_size=6,
        embed_input_length=8192
    )

# Store：构建向量索引
index = VectorStoreIndex(
    nodes,
    embed_model=embed_model
)

# 4️⃣ Retrieve + Generate｜QueryEngine（检索 + 生成）
# 设置 LLM
Settings.llm = OpenAILike(
        model="qwen-plus",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=api_key,
        is_chat_model=True
    )

# 从 Index 构建 QueryEngine
query_engine = index.as_query_engine(
    similarity_top_k=3
)

# 5️⃣ Query｜完整 RAG 调用
response = query_engine.query(
    "这个项目的核心设计目标是什么？"
)
print(response)

# 总结：用这段代码对照 RAG 六步
# Load      → SimpleDirectoryReader → Document
# Split     → SentenceSplitter      → Node
# Embed     → OpenAIEmbedding       → Vector
# Store     → VectorStoreIndex      → Index
# Retrieve  → (implicit Retriever) → TopK Nodes
# Generate  → QueryEngine + LLM     → Response
