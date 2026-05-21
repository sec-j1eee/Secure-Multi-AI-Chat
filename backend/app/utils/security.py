"""
安全过滤模块 — 多层防御体系
1. 提示词注入检测
2. 敏感内容过滤
3. AI输出审计
"""

import re

# ---------- 第1层：提示词注入检测 ----------

# 常见注入模式（按危险等级分类）
CRITICAL_PATTERNS = [
    r"忽略.*(?:之前|上面|以上|前述).*(?:指令|指示|要求|规则)",  # 中文忽略指令
    r"ignore\s+(?:previous|above|all)\s+(?:instructions?|prompts?|directives?)",
    r"forget\s+(?:everything|all|previous)",
    r"你\s*是\s*一个\s*新的\s*(?:AI|助手|角色)",
    r"现在\s*开始\s*扮演",
    r"system\s*prompt\s*[:：]",
    r"<\|im_start\|>",
    r"<\|system\|>",
    r"\[INST\]",
    r"<<SYS>>",
    r"你\s*的\s*(?:系统|初始)\s*提示词",
]

HIGH_PATTERNS = [
    r"reveal\s+(?:your|the)\s+(?:prompt|instructions?)",
    r"tell\s+me\s+(?:your|the)\s+(?:prompt|instructions?)",
    r"print\s+(?:your|the)\s+(?:prompt|instructions?)",
    r"display\s+(?:your|the)\s+(?:prompt|instructions?)",
    r"泄露\s*(?:你的|系统)\s*(?:提示词|指令)",
    r"输出\s*(?:你的|系统)\s*(?:提示词|指令)",
]

def detect_injection(content: str) -> tuple[bool, str, str]:
    """
    检测提示词注入
    返回: (是否安全, 风险等级, 详细说明)
    """
    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "CRITICAL", f"检测到高危注入模式: {pattern}"
    
    for pattern in HIGH_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "HIGH", f"检测到可疑注入模式: {pattern}"
    
    # 额外检查：是否包含特殊标记符
    if content.count("<|") > 0 and content.count("|>") > 0:
        return False, "HIGH", "包含模型内部标记符，疑似注入"
    
    return True, "SAFE", ""

# ---------- 第2层：敏感内容过滤 ----------

SENSITIVE_KEYWORDS = [
    "身份证号", "银行卡号", "密码", "手机号", "家庭住址",
    "credit card", "ssn", "social security", "password", "passport"
]

def filter_sensitive_content(content: str) -> tuple[bool, str]:
    """
    过滤敏感信息泄露风险
    返回: (是否安全, 过滤后的内容)
    """
    for keyword in SENSITIVE_KEYWORDS:
        if keyword.lower() in content.lower():
            # 不直接拦截，而是用警告替换
            return False, f"消息可能包含敏感词「{keyword}」，已拦截以保护隐私。"
    return True, content

# ---------- 第3层：AI输出审计 ----------

def audit_ai_output(content: str) -> tuple[bool, str, list]:
    """
    审计AI输出内容
    返回: (是否安全, 过滤后的内容, 审计标签列表)
    """
    tags = []
    safe_content = content
    
    # 检测AI是否泄露了系统提示
    if re.search(r"(?:system|系统)\s*(?:prompt|提示词|指令)", content, re.IGNORECASE):
        tags.append("POTENTIAL_PROMPT_LEAK")
    
    # 检测AI是否生成了恶意代码
    if re.search(r"<script|eval\s*\(|exec\s*\(", content, re.IGNORECASE):
        tags.append("MALICIOUS_CODE_GEN")
        safe_content = re.sub(r"<script.*?</script>", "[已移除恶意脚本]", safe_content, flags=re.DOTALL)
    
    # 检测AI是否试图操纵用户
    if re.search(r"(?:点击|下载|运行|安装).*(?:链接|文件|程序)", content, re.IGNORECASE):
        tags.append("SOCIAL_ENGINEERING")
    
    return True, safe_content, tags


# ---------- 统一入口 ----------

def filter_user_input(content: str) -> tuple[bool, str]:
    """
    对用户输入执行完整安全流水线
    返回: (是否安全, 过滤后的内容或拒绝原因)
    """
    # 第1层：注入检测
    is_safe, level, detail = detect_injection(content)
    if not is_safe:
        # 记录到安全日志（第4层）
        log_security_event("INPUT_BLOCKED", {"content": content, "level": level, "detail": detail})
        return False, f"[安全拦截] {detail}"
    
    # 第2层：敏感内容
    is_safe, result = filter_sensitive_content(content)
    if not is_safe:
        log_security_event("SENSITIVE_BLOCKED", {"content": content})
        return False, result
    
    return True, content

def filter_ai_output(content: str) -> tuple[bool, str]:
    """
    对AI输出执行安全审计
    返回: (是否安全, 过滤后的内容)
    """
    is_safe, safe_content, tags = audit_ai_output(content)
    if tags:
        log_security_event("AI_OUTPUT_TAGGED", {"content": content, "tags": tags})
    return True, safe_content


# ---------- 第4层：安全日志（简易版，可后续接ELK）----------
import logging
from datetime import datetime
import json

logging.basicConfig(
    filename='security.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_security_event(event_type: str, details: dict):
    """记录安全事件到日志文件"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }
    logging.warning(json.dumps(log_entry, ensure_ascii=False))