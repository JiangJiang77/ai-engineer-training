import uvicorn
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from mcp.server.fastmcp import FastMCP


def create_api_app():
    api_app = FastAPI()

    @api_app.get(
        "/weather",
        operation_id="get_weather",
        description="根据城市名称返回天气描述。当前示例支持北京和上海，其他城市返回未知城市。",
    )
    def get_weather(city: str):
        """查询指定城市的天气信息。"""
        if city == "北京":
            return {"message": "北京天气晴朗"}
        elif city == "上海":
            return {"message": "上海天气多云"}
        else:
            return {"message": "未知城市"}

    @api_app.get(
        "/cloth_recommendation",
        operation_id="get_cloth_recommendation",
        description="根据摄氏温度返回简化的穿衣建议。",
    )
    def get_cloth_recommendation(temperature: float):
        """根据气温推荐合适的穿衣搭配。"""
        if temperature > 30:
            return {"message": "建议穿短袖"}
        elif temperature > 20:
            return {"message": "建议穿长袖"}
        elif temperature > 10:
            return {"message": "建议穿外套"}
        elif temperature > 0:
            return {"message": "建议穿毛衣"}
        else:
            return {"message": "建议穿羽绒服"}

    return api_app


def create_api_mcp_app(api_app: FastAPI):
    fast_api_mcp = FastApiMCP(
        api_app,
        name="My API MCP",
        describe_all_responses=True,  # 在工具描述中包含所有可能的响应模式
        describe_full_response_schema=True,  # 在工具描述中包含完整的 JSON 模式
    )
    fast_api_mcp.mount()

    return fast_api_mcp


def run_mcp_fastapi_demo():
    api_app = create_api_app()
    api_mcp_app = create_api_mcp_app(api_app)
    uvicorn.run(api_app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    run_mcp_fastapi_demo()
