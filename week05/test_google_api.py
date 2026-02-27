import os
from dotenv import load_dotenv

load_dotenv()

print("GOOGLE_API_KEY from env:", os.getenv("GOOGLE_API_KEY"))
print("GOOGLE_API_KEY exists:", "GOOGLE_API_KEY" in os.environ)

# 测试 Google Generative AI
try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    # 方式1：直接传递 API key
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp", google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    print("✅ Model initialized successfully!")

    # 简单测试
    response = model.invoke("Say hello in Chinese")
    print("Response:", response.content)

except Exception as e:
    print(f"❌ Error: {e}")
