import os, sys
from enum import Enum
import json
import logging
from utils.logger import setup_logger

logger = setup_logger(level=logging.DEBUG)

DEBUG = True
config = None
userData = None


class Environment(Enum):
    GITHUBACTION = "GITHUB_ACTION"
    LOCAL = "LOCAL"
    PACKED = "PACKED"

    def __str__(self):
        return self.value


def get_environment():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Environment.PACKED
    elif os.getenv("GITHUB_ACTIONS") == "true":
        return Environment.GITHUBACTION
    else:
        return Environment.LOCAL


def get_config():
    global config

    if config:
        return config

    config = {
        "proxyAddress": os.getenv("PROXY_ADDRESS", ""),
        "messageTemplate": os.getenv("MESSAGE_TEMPLATE", "续火花"),
        "hitokotoTypes": json.loads(
            os.getenv("HITOKOTO_TYPES", '["文学","影视","诗词","哲学"]')
        ),
        "matchMode": os.getenv("MATCH_MODE", "nickname"),
        "browserTimeout": int(os.getenv("BROWSER_TIMEOUT", "120000")),
        "friendListTimeout": int(os.getenv("FRIEND_LIST_WAIT_TIME", "2000")),
        "taskRetryTimes": int(os.getenv("TASK_RETRY_TIMES", "3")),
        "logLevel": os.getenv("LOG_LEVEL", "DEBUG"),
    }

    return config


def sanitize_cookies(cookies):
    for cookie in cookies:
        if "sameSite" in cookie:
            cookie.pop("sameSite")
    return cookies


def get_raw_cookies():
    """从环境变量获取原始cookie字符串（用于base64编码的cookie）"""
    import base64
    raw = os.getenv("COOKIES_FENGZHUORAN_B64", "")
    if raw:
        try:
            decoded = base64.b64decode(raw).decode("utf-8")
            return json.loads(decoded)
        except Exception as e:
            logger.warning(f"Base64 cookie decode failed: {e}, trying plain")
    # Fallback: 尝试直接读取（兼容旧格式）
    raw_plain = os.getenv("COOKIES_FENGZHUORAN", "[]")
    try:
        return json.loads(raw_plain)
    except:
        return []


def get_userData():
    global userData

    if userData:
        return userData

    tasks = json.loads(os.getenv("TASKS", "[]"))

    userData = []

    for task in tasks:
        username = task.get("username", "未知用户")
        unique_id = task.get("unique_id")
        if not unique_id:
            logger.warning(f"{username} 的任务缺少 unique_id 字段，已跳过")
            continue
        
        # 读取COOKIES_FENGZHUORAN环境变量（GitHub Secrets会自动转为大写+下划线格式）
        # GitHub: COOKIES_FENGZHUORAN -> env var: COOKIES__FENGZHUORAN
        cookies_env = os.getenv("COOKIES__FENGZHUORAN") or os.getenv("COOKIES_FENGZHUORAN") or "[]"
        
        try:
            cookies = json.loads(cookies_env)
        except json.JSONDecodeError:
            logger.warning(f"{username} 的 cookies 格式不正确，已跳过")
            continue

        if not cookies:
            logger.warning(f"{username} 的 cookies 为空，已跳过")
            continue

        userData.append(
            {
                "unique_id": unique_id,
                "username": username,
                "cookies": sanitize_cookies(cookies),
                "targets": task.get("targets", []),
            }
        )

    return userData