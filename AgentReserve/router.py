"""
真封装 anet-sdk (Agent-Network-P2P-Service Python SDK)。
需要先 `pip install anet-sdk` 并启动本地 daemon `anet daemon &`。

daemon 默认 REST: http://127.0.0.1:3998
API 参考: https://github.com/zeenaz/Agent-Network-P2P-Service
"""
from __future__ import annotations

import logging
from typing import Any, Iterator, Optional

from anet.svc import SvcClient, SSEEvent

from config import AGENT_NET_ENDPOINT, AGENT_NET_TOKEN, CALL_TIMEOUT

logger = logging.getLogger(__name__)


class AgentNetClient:
    """封装 anet-sdk 的 SvcClient，暴露给 main.py / registrar.py 用。"""

    def __init__(self) -> None:
        kwargs: dict[str, Any] = {"base_url": AGENT_NET_ENDPOINT, "timeout": CALL_TIMEOUT}
        if AGENT_NET_TOKEN:
            kwargs["token"] = AGENT_NET_TOKEN
        self._svc = SvcClient(**kwargs)

    def close(self) -> None:
        try:
            self._svc.close()
        except Exception:
            pass

    # ---------- 注册 ----------
    def register(
        self,
        name: str,
        endpoint: str,
        paths: list[str],
        *,
        tags: Optional[list[str]] = None,
        free: bool = True,
        description: Optional[str] = None,
        health_check: Optional[str] = "/health",
    ) -> dict:
        resp = self._svc.register(
            name=name,
            endpoint=endpoint,
            paths=paths,
            modes=["rr"],
            free=free,
            tags=tags or [],
            description=description,
            health_check=health_check,
        )
        logger.info("registered: %s", resp.get("ans") or resp)
        return resp

    def unregister(self, name: str) -> None:
        try:
            self._svc.unregister(name)
        except Exception as e:
            logger.warning("unregister failed: %s", e)

    # ---------- 发现 ----------
    def discover(self, skill: str, limit: Optional[int] = None) -> list[dict]:
        result = self._svc.discover(skill=skill, limit=limit)
        return result if isinstance(result, list) else []

    # ---------- 同步调用 ----------
    def call(
        self,
        peer_id: str,
        service: str,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        headers: Optional[dict] = None,
        caller_did: Optional[str] = None,
    ) -> dict:
        h = dict(headers or {})
        if caller_did:
            h["X-Agent-DID"] = caller_did
        return self._svc.call(
            peer_id=peer_id,
            service=service,
            path=path,
            method=method,
            body=body,
            headers=h or None,
        )

    # ---------- 流式调用 ----------
    def stream(
        self,
        peer_id: str,
        service: str,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        mode: str = "server-stream",
        headers: Optional[dict] = None,
        caller_did: Optional[str] = None,
    ) -> Iterator[SSEEvent]:
        h = dict(headers or {})
        if caller_did:
            h["X-Agent-DID"] = caller_did
        return self._svc.stream(
            peer_id=peer_id,
            service=service,
            path=path,
            method=method,
            body=body,
            mode=mode,
            headers=h or None,
            timeout=None,
        )
