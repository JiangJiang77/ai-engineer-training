"""政策相关工具"""
from langchain_core.tools import tool
from smart_customer_service.utils import get_logger

logger = get_logger(__name__)


@tool
def search_policy_tool(query: str) -> str:
    """搜索公司政策文档。输入: 查询关键词。示例: 退货政策 或 发票规则 或 保修期。输出: 匹配的政策内容或提示。"""
    try:
        from smart_customer_service.rag import load_documents, VectorStoreManager

        query = query.strip()
        logger.debug(f"[Tool] SearchPolicy: query={query}")

        vector_store = VectorStoreManager()
        if not vector_store.load_vectorstore():
            documents = load_documents()
            if not documents:
                return "政策文档加载失败"
            vector_store.create_vectorstore(documents)

        docs = vector_store.similarity_search(query, k=3)

        if not docs:
            return "未找到相关政策信息"

        result = "\n\n".join(
            [
                f"【{doc.metadata.get('type', '文档')}】\n{doc.page_content}"
                for doc in docs
            ]
        )

        return result

    except Exception as e:
        logger.error(f"[Tool Error] SearchPolicy: {e}", exc_info=True)
        return f"政策查询失败: {str(e)}"


def create_policy_tools() -> list:
    """创建政策相关工具列表"""
    tools = [search_policy_tool]
    logger.debug(f"创建了 {len(tools)} 个政策工具: {[t.name for t in tools]}")
    return tools
