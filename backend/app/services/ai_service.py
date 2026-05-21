import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 中的环境变量

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

GLM_API_KEY = os.getenv("GLM_API_KEY")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

async def call_deepseek(history: list[dict], system_prompt: str = "你是一个群聊中的AI助手，请结合历史对话给出专业的回答。") -> str:
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
        "max_tokens": 2048
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
    
async def call_glm(history: list[dict], system_prompt: str = "你是一个群聊中的AI助手，请结合历史对话给出专业的回答。") -> str:
    """调用智谱 GLM-4 API"""
    headers = {
        "Authorization": f"Bearer {GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [{"role": "system", "content": system_prompt}] + history
    payload = {
        "model": "glm-4",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{GLM_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

# 统一调度器
MODEL_MAP = {
    "@DeepSeek": call_deepseek,
    "@GLM": call_glm,
    # 未来添加新模型只需在这里注册
}

async def call_ai(model_name: str, history: list[dict], system_prompt: str = "你是一个乐于助人的AI助手。") -> str:
    """
    根据模型名分发请求
    :param model_name: 用户输入的 @模型名，如 "@DeepSeek" 或 "@GLM"
    """
    if model_name in MODEL_MAP:
        return await MODEL_MAP[model_name](history, system_prompt)
    else:
        return f"未知的AI模型：{model_name}"