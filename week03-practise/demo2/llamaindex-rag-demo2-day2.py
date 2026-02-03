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
    chunk_size=256,
    chunk_overlap=50
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

# 辅助函数：格式化输出问题和答案
def ask_and_print(query_engine, question, category=""):
    """
    发起查询并格式化输出问题和答案
    
    Args:
        query_engine: 查询引擎
        question: 问题文本
        category: 问题分类（可选）
    """
    if category:
        # print(f"\n{'='*80}")
        print(f"类别：【{category}】")
        # print(f"{'='*80}")
    
    print(f"❓ 问题: {question}")
    # print(f"{'-'*80}")
    response = query_engine.query(question)
    print(f"💡 答案: {response}")
    print(f"{'='*50}\n")
    return response

# 5️⃣ Query｜完整 RAG 调用
ask_and_print(query_engine, "这个项目的核心设计目标是什么？", "初始测试")

######周期流量（车道级）语义完整度问题
ask_and_print(query_engine, "周期流量-车道的计算输入包括哪些数据？", "周期流量（车道级）语义完整度问题")
ask_and_print(query_engine, "在周期流量-车道计算中，当一个车道对应多个流向时，采用什么计算逻辑？")
ask_and_print(query_engine, "周期流量-车道计算中，为什么会出现'跨周期'的相位时间计算？")

######红绿灯末排队（车道级）语义完整度问题
ask_and_print(query_engine, "车道红灯末排队长度是如何计算的？在有无待行区时有什么区别？", "红绿灯末排队（车道级）语义完整度问题")
ask_and_print(query_engine, "为什么绿灯末排队使用'中位数'而不是最大值？")
ask_and_print(query_engine, "在红绿灯末排队计算中，置信度 A1 数据连续性异常的判定规则是什么？")

######五分钟间隔流量（车道级）语义完整度问题
ask_and_print(query_engine, "五分钟车道流量在多数据源同时存在时，数据源的默认优先级是什么？", "五分钟间隔流量（车道级）语义完整度问题")
ask_and_print(query_engine, "如果高优先级数据源无数据，系统是如何处理的？")
ask_and_print(query_engine, "在非深夜时段出现 0 流量时，置信度是如何处理的？")

######通行能力（车道级）语义完整度问题
ask_and_print(query_engine, "车道通行能力在早晚高峰时段采用的是哪一种分位值？", "通行能力（车道级）语义完整度问题")
ask_and_print(query_engine, "什么情况下会采用国标默认通行能力值？默认值是多少？")
ask_and_print(query_engine, "为什么计算得到的通行能力需要与默认值进行比较并修正？")

######1️⃣ 周期流量类（稳定性问题组）
ask_and_print(query_engine, "周期流量-车道是如何计算的？", "1️⃣ 周期流量类（稳定性问题组）")
ask_and_print(query_engine, "车道在一个信号周期内的流量统计规则是什么？")
ask_and_print(query_engine, "周期车道流量的统计时间范围如何确定？")

######2️⃣ 排队与置信度类（稳定性问题组）
ask_and_print(query_engine, "红绿灯末排队的置信度是怎么计算的？", "2️⃣ 排队与置信度类（稳定性问题组）")
ask_and_print(query_engine, "哪些异常情况会影响排队数据的置信度？")
ask_and_print(query_engine, "排队数据中有哪些物理校验规则？")

######3️⃣ 五分钟流量类（稳定性问题组）
ask_and_print(query_engine, "五分钟车道流量是如何确定的？", "3️⃣ 五分钟流量类（稳定性问题组）")
ask_and_print(query_engine, "多数据源五分钟流量如何融合？")
ask_and_print(query_engine, "五分钟流量置信度中，超流量上限是如何扣分的？")

# ######4️⃣ 路径与高饱和算法（稳定性问题组）
# ask_and_print(query_engine, "路径高饱和路口筛选算法的目的是什么？", "4️⃣ 路径与高饱和算法（稳定性问题组）")
# ask_and_print(query_engine, "为什么要先按流量筛选，再按饱和度筛选？")
# ask_and_print(query_engine, "高饱和流向筛选时，对数量有什么下限要求？")



# 总结：用这段代码对照 RAG 六步
# Load      → SimpleDirectoryReader → Document
# Split     → SentenceSplitter      → Node
# Embed     → OpenAIEmbedding       → Vector
# Store     → VectorStoreIndex      → Index
# Retrieve  → (implicit Retriever) → TopK Nodes
# Generate  → QueryEngine + LLM     → Response

# | 配置 | chunk / overlap | Node 数量 | 语义完整度 | 回答稳定性 |
# | -- | --------------- | ------- | ----- | ----- |
# | A  | 512 / 100       | 38 nodes|       |       |
# | B  | 800 / 0         |         |       |       |
# | C  | 300 / 50        |         |       |       |

