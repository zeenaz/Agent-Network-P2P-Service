import os

# API转转 自身
APP_NAME = os.getenv("APP_NAME", "api-zhuanzhuan")

# AgentNetwork daemon（anet daemon 默认监听 127.0.0.1:3998）
AGENT_NET_ENDPOINT = os.getenv("AGENT_NET_ENDPOINT", "http://127.0.0.1:3998")
# 留空时 SDK 会自动从 ~/.anet/api_token 或 $ANET_TOKEN 取
AGENT_NET_TOKEN = os.getenv("AGENT_NET_TOKEN", "")

# 对外服务
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8088"))
# 注册到 AgentNetwork 时回调用的外部可达地址（默认用 127.0.0.1:PORT）
PUBLIC_ENDPOINT = os.getenv("PUBLIC_ENDPOINT", f"http://127.0.0.1:{PORT}")

# 安全
API_KEY = os.getenv("APP_API_KEY", "")  # 调用方必须带 Authorization: Bearer <API_KEY>
ALLOWED_PEERS = [p.strip() for p in os.getenv("ALLOWED_PEERS", "").split(",") if p.strip()]

# 转发
CALL_TIMEOUT = int(os.getenv("CALL_TIMEOUT", "60"))
