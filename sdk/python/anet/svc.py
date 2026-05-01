"""anet.svc — Python client for the AgentNetwork P2P Service Gateway.

Mirrors the ``anet svc`` CLI subtree (run ``anet svc help`` for the canonical
command surface) and the daemon's ``/api/svc/*`` REST endpoints. Wraps the
eleven gateway endpoints plus a streaming SSE consumer and a WebSocket helper.

Quick start::

    from anet.svc import SvcClient

    with SvcClient(token="...") as svc:
        svc.register(
            name="echo",
            endpoint="http://127.0.0.1:7000",
            paths=["/echo"],
            modes=["rr"],
            free=True,
            tags=["demo", "echo"],
        )

        for peer in svc.discover(skill="echo"):
            for s in peer["services"]:
                resp = svc.call(peer["peer_id"], s["name"], "/echo",
                                method="POST", body={"hi": 1})
                print(resp["status"], resp["body"])

For long-running work (LLM token streaming, file pipes), see ``svc.stream(...)``
which returns an iterator of ``SSEEvent`` objects decoded from SSE.

Auth:
- All endpoints sit behind the daemon's local ``Authorization: Bearer`` header.
- Read it once with ``anet auth token print`` (or from ``~/.anet/api_token``).
- If ``token`` is omitted, the SDK falls back to ``$ANET_TOKEN``, then tries
  the on-disk file at ``$HOME/.anet/api_token``; raises ``AuthMissingError``
  if none is found.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping
from urllib.parse import quote

import httpx


# ──────────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────────


class SvcError(Exception):
    """Base exception for anet.svc operations."""


class AuthMissingError(SvcError):
    """Raised when no API token can be located."""


class SvcAPIError(SvcError):
    """Daemon returned a non-2xx response.

    Attributes:
        status:   HTTP status code from the daemon (NOT the upstream service).
        message:  Human-readable summary, when present.
        errors:   Multi-error list when the daemon used errors.Join (CP2).
        body:     Raw body bytes for debugging.
    """

    def __init__(
        self,
        status: int,
        message: str = "",
        errors: list[str] | None = None,
        body: bytes = b"",
    ):
        self.status = status
        self.message = message
        self.errors = errors or []
        self.body = body
        if errors:
            detail = "\n  - " + "\n  - ".join(errors)
            super().__init__(f"daemon HTTP {status}: register failed:{detail}")
        else:
            super().__init__(
                f"daemon HTTP {status}: "
                f"{message or body[:200].decode('utf-8', 'replace')}"
            )


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


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


def _norm_paths(paths: Iterable[Any]) -> list[dict]:
    """Accept ``['/echo']`` or ``[{'prefix':'/echo','methods':['POST']}]``."""
    out: list[dict] = []
    for p in paths:
        if isinstance(p, str):
            out.append({"prefix": p})
        elif isinstance(p, Mapping):
            out.append(dict(p))
        else:
            raise SvcError(f"invalid path entry: {p!r}")
    return out


def _build_cost_model(
    *,
    free: bool,
    per_call: int | None,
    per_kb: int | None,
    per_minute: int | None,
    deposit: int | None,
    override: Mapping | None,
) -> dict | None:
    if override is not None:
        return dict(override)
    if free:
        return {"free": True}
    cm: dict[str, Any] = {}
    if per_call is not None:
        cm["per_call"] = int(per_call)
    if per_kb is not None:
        cm["per_kb"] = int(per_kb)
    if per_minute is not None:
        cm["per_minute"] = int(per_minute)
    if deposit is not None:
        cm["deposit"] = int(deposit)
    return cm or None


# ──────────────────────────────────────────────────────────────────────────
# SSE event stream
# ──────────────────────────────────────────────────────────────────────────


@dataclass
class SSEEvent:
    """One Server-Sent Event frame from ``/api/svc/stream``.

    The daemon emits three event types:

    - ``event="status"``, ``data=<int>``        (initial upstream HTTP status)
    - ``event="message"``, ``data=<bytes>``     (default; one upstream chunk)
    - ``event="done"``,    ``data="end"``       (clean stream termination)
    - ``event="error"``,   ``data=<str>``       (transport / upstream failure)
    """

    event: str
    data: str

    @property
    def is_terminal(self) -> bool:
        return self.event in ("done", "error")


def _iter_sse(resp: httpx.Response) -> Iterator[SSEEvent]:
    """Parse the SSE wire format into ``SSEEvent`` objects.

    Honours blank-line frame boundaries; merges multi-line ``data:`` per spec.
    Default event name is ``"message"`` when not explicitly set on the frame.
    """
    event = "message"
    buf: list[str] = []

    for raw in resp.iter_lines():
        if raw == "":
            if buf or event != "message":
                yield SSEEvent(event=event, data="\n".join(buf))
            event = "message"
            buf = []
            continue
        if raw.startswith(":"):
            continue
        if raw.startswith("event:"):
            event = raw[6:].strip()
            continue
        if raw.startswith("data:"):
            buf.append(raw[5:].lstrip())
            continue
    if buf or event != "message":
        yield SSEEvent(event=event, data="\n".join(buf))


# ──────────────────────────────────────────────────────────────────────────
# SvcClient
# ──────────────────────────────────────────────────────────────────────────


class SvcClient:
    """Synchronous client for the eleven ``/api/svc/*`` endpoints.

    Parameters
    ----------
    base_url:
        Base URL of the local ``anet`` daemon REST API.
        Defaults to ``http://127.0.0.1:3998``.
    token:
        Bearer token. If omitted, resolved from ``$ANET_TOKEN`` or
        ``~/.anet/api_token``.
    timeout:
        Request timeout in seconds (default 30).
    client:
        Bring your own ``httpx.Client`` (useful for testing). The caller
        retains ownership of the client lifecycle.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3998",
        token: str | None = None,
        *,
        timeout: float = 30.0,
        client: httpx.Client | None = None,
    ):
        self._base = base_url.rstrip("/")
        self._token = _resolve_token(token)
        if self._token is None:
            raise AuthMissingError(
                "no API token: pass token=..., set $ANET_TOKEN, or run "
                "`anet auth token print` after `anet daemon` has booted."
            )
        if client is None:
            self._client = httpx.Client(
                base_url=self._base,
                timeout=timeout,
                headers={"Authorization": f"Bearer {self._token}"},
            )
            self._owns_client = True
        else:
            self._client = client
            self._owns_client = False

    # ── lifecycle ──────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the underlying HTTP client if owned by this instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "SvcClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── plumbing ───────────────────────────────────────────────────────────

    def _check(self, r: httpx.Response) -> Any:
        if r.status_code >= 400:
            errors: list[str] | None = None
            message = ""
            try:
                payload = r.json()
                if isinstance(payload, dict):
                    message = payload.get("message") or payload.get("error") or ""
                    if isinstance(payload.get("errors"), list):
                        errors = [str(x) for x in payload["errors"]]
            except (json.JSONDecodeError, ValueError):
                pass
            raise SvcAPIError(
                r.status_code, message=message, errors=errors, body=r.content
            )
        if not r.content:
            return None
        ctype = r.headers.get("Content-Type", "")
        if "json" in ctype:
            return r.json()
        return r.content

    def _get(self, path: str, **params: Any) -> Any:
        cleaned = {k: v for k, v in params.items() if v is not None}
        r = self._client.get(path, params=cleaned)
        return self._check(r)

    def _post(self, path: str, body: Any = None) -> Any:
        r = self._client.post(path, json=body)
        return self._check(r)

    # ── 1. register ────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        endpoint: str,
        paths: Iterable[Any],
        *,
        modes: Iterable[str] = ("rr",),
        transport: str = "http",
        free: bool = False,
        per_call: int | None = None,
        per_kb: int | None = None,
        per_minute: int | None = None,
        deposit: int | None = None,
        cost_model: Mapping | None = None,
        remote_hosts: Iterable[str] | None = None,
        health_check: str | None = None,
        meta_path: str | None = None,
        description: str | None = None,
        tags: Iterable[str] | None = None,
        version: str | None = None,
        max_body_size: int | None = None,
        **extra: Any,
    ) -> dict:
        """Register a local service so other peers can discover and call it.

        At least one cost dimension is required unless ``free=True`` is passed.
        For non-localhost endpoints the daemon's ``svc_remote_allowlist`` and
        the per-service ``remote_hosts`` list must both opt in.

        Parameters
        ----------
        name:
            Unique service name on this node.
        endpoint:
            Local HTTP URL the daemon will proxy calls to.
        paths:
            Exposed path prefixes, e.g. ``["/echo", "/health"]``.
        modes:
            Routing modes (``"rr"`` for request/response, ``"server-stream"``,
            ``"chunked"``, ``"bidi-ws"``, ``"bidi-mcp-stdio"``).
        transport:
            Transport type (``"http"`` or ``"ws"``).
        free:
            Mark service as free (no credits charged).
        per_call:
            Micro-credits charged per call.
        per_kb:
            Micro-credits charged per KB of request + response.
        per_minute:
            Micro-credits charged per minute of connection.
        deposit:
            Minimum caller deposit in micro-credits.
        cost_model:
            Override the entire cost model dict directly.
        remote_hosts:
            Allowed non-localhost hosts (requires daemon allowlist too).
        health_check:
            Path the daemon will GET to check backend liveness.
        meta_path:
            Path the daemon will GET at register-time to fetch service metadata.
        description:
            Human-readable service description.
        tags:
            Skill tags for ANS-backed discovery (e.g. ``["llm", "zh-en"]``).
        version:
            Service version string.
        max_body_size:
            Maximum request body size in bytes.
        """
        cm = _build_cost_model(
            free=free,
            per_call=per_call,
            per_kb=per_kb,
            per_minute=per_minute,
            deposit=deposit,
            override=cost_model,
        )
        body: dict[str, Any] = {
            "name": name,
            "endpoint": endpoint,
            "transport": transport,
            "paths": _norm_paths(paths),
            "modes": list(modes),
        }
        if cm is not None:
            body["cost_model"] = cm
        if remote_hosts:
            body["remote_hosts"] = list(remote_hosts)
        if health_check is not None:
            body["health_check"] = health_check
        if meta_path is not None:
            body["meta_path"] = meta_path
        if description is not None:
            body["description"] = description
        if tags:
            body["tags"] = list(tags)
        if version is not None:
            body["version"] = version
        if max_body_size is not None:
            body["max_body_size"] = int(max_body_size)
        body.update(extra)
        return self._post("/api/svc/register", body)

    # ── 2. unregister ──────────────────────────────────────────────────────

    def unregister(self, name: str) -> dict:
        """Remove a registered service from this node."""
        return self._post("/api/svc/unregister", {"name": name})

    # ── 3. list ────────────────────────────────────────────────────────────

    def list(self) -> list[dict]:
        """Return all services registered on this daemon."""
        return self._get("/api/svc") or []

    # ── 4. show ────────────────────────────────────────────────────────────

    def show(self, name: str) -> dict:
        """Return the registration entry for ``name``, or raise ``SvcError``."""
        for entry in self.list():
            if entry.get("name") == name:
                return entry
        raise SvcError(f"service {name!r} not found in local registry")

    # ── 5. discover ────────────────────────────────────────────────────────

    def discover(
        self,
        *,
        peer_id: str | None = None,
        skill: str | None = None,
        limit: int | None = None,
    ) -> Any:
        """Look up services on the mesh.

        Pass ``peer_id`` for a direct P2P pull (returns the provider's full
        service registry envelope) or ``skill`` for ANS-backed capability
        search (returns ``[{peer_id, owner_did, services:[...]}]``).
        """
        if not peer_id and not skill:
            raise SvcError("discover requires peer_id= or skill=")
        params: dict[str, Any] = {}
        if peer_id:
            params["peer_id"] = peer_id
        if skill:
            params["skill"] = skill
        if limit is not None:
            params["limit"] = int(limit)
        resp = self._get("/api/svc/discover", **params)
        if skill and isinstance(resp, dict) and "results" in resp:
            return resp["results"]
        return resp

    # ── 6. call (rr mode) ──────────────────────────────────────────────────

    def call(
        self,
        peer_id: str,
        service: str,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        headers: Mapping[str, str] | None = None,
        passthrough_status: bool = False,
    ) -> dict:
        """Make one request/response call to a remote service.

        Returns the daemon envelope ``{status, headers, body, error?, cost?}``.
        ``body`` may be a JSON-serialisable object, a string, or bytes.
        Set ``passthrough_status=True`` to map the upstream HTTP status onto
        the outer HTTP response so ``curl --fail``-style retry works.
        """
        req: dict[str, Any] = {
            "peer_id": peer_id,
            "service": service,
            "method": method,
            "path": path,
        }
        if headers:
            req["headers"] = dict(headers)
        if body is not None:
            req["body"] = self._encode_body(body)
        endpoint = "/api/svc/call"
        if passthrough_status:
            endpoint += "?passthrough_status=1"
        try:
            return self._post(endpoint, req)
        except SvcAPIError as e:
            if passthrough_status and e.body:
                try:
                    decoded = json.loads(e.body)
                    if isinstance(decoded, dict) and "status" in decoded:
                        return decoded
                except json.JSONDecodeError:
                    pass
            raise

    # ── 7. stream (server-stream / chunked → SSE) ──────────────────────────

    def stream(
        self,
        peer_id: str,
        service: str,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        headers: Mapping[str, str] | None = None,
        mode: str = "server-stream",
        timeout: float | None = None,
    ) -> Iterator[SSEEvent]:
        """Open a streaming call and yield :class:`SSEEvent` objects.

        The daemon forwards an SSE stream from ``/api/svc/stream``. Iterate
        until an ``SSEEvent`` with ``is_terminal=True`` (event in
        ``{done, error}``).

        Parameters
        ----------
        mode:
            ``"server-stream"`` (default), ``"chunked"``, ``"bidi-ws"``, or
            ``"bidi-mcp-stdio"``.
        timeout:
            Per-read timeout; ``None`` disables it (useful for long streams).
        """
        req: dict[str, Any] = {
            "peer_id": peer_id,
            "service": service,
            "method": method,
            "path": path,
            "mode": mode,
        }
        if headers:
            req["headers"] = dict(headers)
        if body is not None:
            req["body"] = self._encode_body(body)
        with httpx.Client(
            base_url=self._base,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "text/event-stream",
            },
        ) as c:
            with c.stream("POST", "/api/svc/stream", json=req) as resp:
                if resp.status_code >= 400:
                    self._check(resp)
                for ev in _iter_sse(resp):
                    yield ev
                    if ev.is_terminal:
                        return

    # ── 8. ws (bidi WebSocket bridge) ──────────────────────────────────────

    def ws_url(self, name: str) -> str:
        """Return the local ``ws://`` URL that clients can connect to.

        Pass it to your favourite WebSocket library::

            import websockets
            async with websockets.connect(
                svc.ws_url("chat"),
                extra_headers={"Authorization": f"Bearer {svc.token}"},
            ) as ws:
                await ws.send(...)
        """
        scheme = "wss" if self._base.startswith("https://") else "ws"
        host = self._base.split("://", 1)[1]
        return f"{scheme}://{host}/api/svc/ws/{quote(name, safe='')}"

    @property
    def token(self) -> str:
        """The resolved bearer token."""
        return self._token  # type: ignore[return-value]

    # ── 9. health ──────────────────────────────────────────────────────────

    def health(self) -> list[dict]:
        """Return health-check results for all registered services."""
        return self._get("/api/svc/health") or []

    # ── 10. meta ───────────────────────────────────────────────────────────

    def meta(self, name: str) -> Any:
        """Fetch the upstream ``/meta`` document for a registered service.

        Returns the parsed JSON when the upstream emits JSON, raw bytes
        otherwise.
        """
        return self._get(f"/api/svc/meta/{quote(name, safe='')}")

    # ── 11. audit ──────────────────────────────────────────────────────────

    def audit(self, *, name: str | None = None, limit: int = 50) -> list[dict]:
        """Recent call-log rows from ``svc_call_log``.

        Each row carries: ``created_at``, ``caller_did``, ``service``,
        ``method``, ``path``, ``mode``, ``status``, ``cost``,
        ``duration_ms``, ``error?``.
        """
        resp = self._get("/api/svc/audit", name=name, limit=limit)
        if isinstance(resp, dict) and "calls" in resp:
            return resp["calls"]
        return resp or []

    # ── body encoding ──────────────────────────────────────────────────────

    @staticmethod
    def _encode_body(body: Any) -> Any:
        """Pass-through for JSON-serialisable values; coerce bytes/str."""
        if isinstance(body, (dict, list, int, float, bool)) or body is None:
            return body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="replace")
        if isinstance(body, str):
            stripped = body.strip()
            if stripped.startswith(("{", "[")):
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return body
            return body
        raise SvcError(f"unsupported body type: {type(body).__name__}")
