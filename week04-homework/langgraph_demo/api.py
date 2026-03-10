from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from .services import service_manager
from .graph import GraphManager
from .tool import get_order_detail, get_policy_detail

app = FastAPI(
    title="智能客服助手",
    description="基于LangGraph的智能客服助手API",
    version="1.0.0",
)

graph_manager = GraphManager(service_manager)


class ChatRequest(BaseModel):
    user_id: str # 用于追踪会话
    content: str


class HotUpdateRequest(BaseModel):
    tool_type: str # "query_tool" or "policy_tool" or "all_tool"
    model_name: str # e.g., "qwen-max" or "default"

@app.post("/chat",summary="对话接口")
async def chat(request: ChatRequest):
    """
    对话接口
    """
    thread_id = request.user_id
    config = {"configurable": {"thread_id": thread_id}}
    user_input = request.content
    
    messages = [HumanMessage(content=request.content)]

    final_answer = graph_manager.invoke_workflow(user_input,config)
    final_answer =  "抱歉，我暂时无法处理这个问题" if not final_answer else final_answer
    return {"response": final_answer,"user_id": thread_id}

@app.get("/healthy",summary="健康检查接口")
async def healthy():
    """
    健康检查接口
    """
    service_status = graph_manager.get_service_status()
    return {"status": "healthy","services": service_status}

@app.post("/hot_update",summary="热更新接口")
async def hot_update(request: HotUpdateRequest):
    """
    热更新接口
    """
    try:
        tool_type = request.tool_type
        model_name = request.model_name
        
        if model_name:
            service_manager.update_llm(model_name)
        
        if tool_type == "query_tool":
            tools = [get_order_detail]
        elif tool_type == "policy_tool":
            tools = [get_policy_detail]
        elif tool_type == "all_tool":
            tools = [get_order_detail, get_policy_detail]
        else:
            raise HTTPException(status_code=400, detail="无效的更新类型")

        service_manager.update_tools(tools)

        graph_manager.reload_graph()

        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"热更新失败: {e}")

# 如果你想通过 python -m smart_customer_service_extend.api 运行
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)