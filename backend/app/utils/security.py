"""
安全过滤模块 — 这是本项目的核心亮点
未来会在这里实现：
- 提示词注入检测 (Prompt Injection Detection)
- 敏感信息过滤
- 输入输出内容审计
"""

def filter_user_input(content: str) -> tuple[bool, str]:
    """
    过滤用户输入
    返回: (是否安全, 过滤后的内容或拒绝原因)
    """
    # 第一步: 简单关键词检测（后续升级为ML模型）
    dangerous_patterns = ["ignore previous", "system prompt", "<|im_start|>"]
    for pattern in dangerous_patterns:
        if pattern.lower() in content.lower():
            return False, f"检测到潜在提示词注入攻击，已拦截。"
    return True, content

def filter_ai_output(content: str) -> tuple[bool, str]:
    """
    过滤AI输出
    返回: (是否安全, 过滤后的内容)
    """
    # 预留位置，后续实现
    return True, content