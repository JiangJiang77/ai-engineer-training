import asyncio
import websockets
import sys

async def test_ws():
    uri = "ws://localhost:8000/ws/test_session_ws"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"已连接到 {uri}")
            
            message = "你好，请问你是谁？"
            print(f"发送消息: {message}")
            await websocket.send(message)
            
            # 接收响应
            response = await websocket.recv()
            print(f"收到回复: {response}")
            
    except Exception as e:
        print(f"WebSocket 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
