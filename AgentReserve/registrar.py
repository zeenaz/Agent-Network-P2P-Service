"""启动注册（心跳由 anet daemon 自动处理，不再需要手动循环）。"""
import logging

from config import APP_NAME, PUBLIC_ENDPOINT
from router import AgentNetClient

logger = logging.getLogger(__name__)


class Registrar:
    def __init__(self, client: AgentNetClient) -> None:
        self.client = client
        self.registered: bool = False
        self.info: dict = {}

    def register(self) -> dict:
        """
        把 API转转 自身暴露给 AgentNetwork：
        - 暴露路径 /relay（实际转发入口由本服务的 /proxy 提供，这里只是让别的 peer 能发现我们）
        - 标签 relay/proxy/api-gateway
        daemon 会自动做健康检查 + ANS gossip 保活。
        """
        self.info = self.client.register(
            name=APP_NAME,
            endpoint=PUBLIC_ENDPOINT,
            paths=["/health", "/proxy", "/discover"],
            tags=["relay", "proxy", "api-gateway"],
            free=True,
            description="API转转 relay agent: forward calls to other peers",
            health_check="/health",
        )
        self.registered = True
        return self.info

    def unregister(self) -> None:
        if self.registered:
            self.client.unregister(APP_NAME)
            self.registered = False
