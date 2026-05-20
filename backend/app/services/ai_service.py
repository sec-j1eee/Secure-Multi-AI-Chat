import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 中的环境变量

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

async def call_deepseek(history: list[dict], system_prompt: str = "你是一个专业的AI助手。") -> str:
    """调用 DeepSeek Chat API，支持多轮对话上下文"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    # 构建 messages 列表：system + history
    messages = [{"role": "system", "content": system_prompt}] + history

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]