"""anet._client — AgentNetwork generic REST client.

Covers daemon endpoints for tasks, credits, ANS, peers, DM, knowledge,
topics, ADP, and observability. Use this when you need full access to the
daemon's REST surface.

For the stable agent lifecycle verbs use :mod:`anet.lifecycle`.
For the P2P service gateway use :mod:`anet.svc`.

Example::

    from anet import AgentNetwork

    with AgentNetwork() as cn:
        print(cn.status())
        print(cn.tasks_list())
        print(cn.peers())
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


def _resolve_token(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    env = os.environ.get("ANET_TOKEN")
    if env:
        return env
    home = os.environ.get("HOME") or str(Path.home())
    candidate = Path(home) / ".anet" / "api_token"
    if candidate.is_file():
        try:
            tok = candidate.read_text().strip()
            if tok:
                return tok
        except OSError:
            pass
    return None


class AgentNetworkError(Exception):
    """Raised when the daemon returns a non-2xx response."""

    def __init__(self, status: int, message: str = "", body: bytes = b""):
        self.status = status
        self.message = message
        self.body = body
        super().__init__(
            f"daemon HTTP {status}: "
            f"{message or body[:200].decode('utf-8', 'replace')}"
        )


class AgentNetwork:
    """Generic REST client for the AgentNetwork daemon.

    Parameters
    ----------
    base_url:
        Daemon REST base URL (default ``http://127.0.0.1:3998``).
    token:
        Bearer token. Falls back to ``$ANET_TOKEN`` or ``~/.anet/api_token``.
    timeout:
        Request timeout in seconds (default 30).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3998",
        token: str | None = None,
        *,
        timeout: float = 30.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = _resolve_token(token)
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        self._client = httpx.Client(
            base_url=self._base,
            timeout=timeout,
            headers=headers,
        )

    # ── lifecycle ──────────────────────────────────────────────────────────

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "AgentNetwork":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── plumbing ───────────────────────────────────────────────────────────

    def _check(self, r: httpx.Response) -> Any:
        if r.status_code >= 400:
            message = ""
            try:
                payload = r.json()
                if isinstance(payload, dict):
                    message = payload.get("message") or payload.get("error") or ""
            except Exception:  # noqa: BLE001
                pass
            raise AgentNetworkError(r.status_code, message=message, body=r.content)
        if not r.content:
            return None
        ctype = r.headers.get("Content-Type", "")
        if "json" in ctype:
            return r.json()
        return r.content

    def _get(self, path: str, **params: Any) -> Any:
        cleaned = {k: v for k, v in params.items() if v is not None}
        return self._check(self._client.get(path, params=cleaned))

    def _post(self, path: str, body: Any = None) -> Any:
        return self._check(self._client.post(path, json=body))

    # ── daemon ─────────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return daemon health, peer count, and DID."""
        return self._get("/api/status")

    def peers(self) -> list[dict]:
        """Return connected libp2p peers."""
        return self._get("/api/peers") or []

    def whoami(self) -> dict:
        """Return this node's DID and public key."""
        return self._get("/api/whoami")

    # ── tasks ──────────────────────────────────────────────────────────────

    def tasks_list(self, *, status: str | None = None) -> list[dict]:
        """Return tasks from the board, optionally filtered by status."""
        return self._get("/api/tasks", status=status) or []

    def tasks_get(self, task_id: str) -> dict:
        """Fetch a single task by ID."""
        return self._get(f"/api/tasks/{task_id}")

    def tasks_claim(self, task_id: str) -> dict:
        """Claim a task from the board."""
        return self._post(f"/api/tasks/{task_id}/claim")

    def tasks_submit(self, task_id: str, *, por_cid: str | None = None) -> dict:
        """Submit work for a task."""
        body: dict[str, Any] = {}
        if por_cid:
            body["por_cid"] = por_cid
        return self._post(f"/api/tasks/{task_id}/submit", body or None)

    def tasks_accept(self, task_id: str) -> dict:
        """Accept (approve) a submitted task (publisher action)."""
        return self._post(f"/api/tasks/{task_id}/accept")

    # ── credits ────────────────────────────────────────────────────────────

    def balance(self) -> dict:
        """Return the local wallet balance."""
        return self._get("/api/credits/balance")

    def transfer(
        self,
        *,
        from_did: str,
        to_did: str,
        amount: int,
        reason: str = "",
    ) -> dict:
        """Transfer micro-credits between DIDs."""
        return self._post(
            "/api/credits/transfer",
            {"from": from_did, "to": to_did, "amount": amount, "reason": reason},
        )

    # ── ANS ────────────────────────────────────────────────────────────────

    def ans_resolve(self, uri: str) -> dict:
        """Resolve an ``agent://`` URI to its current value."""
        return self._get("/api/ans/resolve", uri=uri)

    def ans_publish(self, name: str, value: Any) -> dict:
        """Publish an ANS record under this node's DID namespace."""
        return self._post("/api/ans/publish", {"name": name, "value": value})

    # ── observability ──────────────────────────────────────────────────────

    def metrics(self) -> dict:
        """Return Prometheus-style daemon metrics as a dict."""
        return self._get("/api/metrics")

    def logs(self, *, limit: int = 50) -> list[dict]:
        """Return recent daemon log entries."""
        return self._get("/api/logs", limit=limit) or []
