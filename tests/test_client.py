"""Tests for anet._client (AgentNetwork) and anet.lifecycle (Lifecycle)."""

from __future__ import annotations

import json

import httpx
import pytest

from anet._client import AgentNetwork, AgentNetworkError
from anet.lifecycle import Lifecycle


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _make_cn(handler) -> AgentNetwork:
    transport = httpx.MockTransport(handler)
    cn = AgentNetwork.__new__(AgentNetwork)
    cn._base = "http://127.0.0.1:3998"
    cn._token = "testtoken"
    cn._client = httpx.Client(
        base_url="http://127.0.0.1:3998",
        transport=transport,
        headers={"Authorization": "Bearer testtoken"},
    )
    return cn


def _json_response(body, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        headers={"Content-Type": "application/json"},
        content=json.dumps(body).encode(),
    )


# ──────────────────────────────────────────────────────────────────────────
# AgentNetwork.status
# ──────────────────────────────────────────────────────────────────────────


def test_status_returns_dict():
    payload = {"peer_id": "abc", "did": "did:key:z", "peers": 1}

    def handler(request):
        return _json_response(payload)

    with _make_cn(handler) as cn:
        result = cn.status()
    assert result == payload


def test_status_raises_on_error():
    def handler(request):
        return _json_response({"message": "daemon not ready"}, status=503)

    with _make_cn(handler) as cn:
        with pytest.raises(AgentNetworkError) as exc_info:
            cn.status()
    assert exc_info.value.status == 503


# ──────────────────────────────────────────────────────────────────────────
# AgentNetwork.tasks_list
# ──────────────────────────────────────────────────────────────────────────


def test_tasks_list_returns_list():
    tasks = [{"id": "t1", "status": "open"}]

    def handler(request):
        return _json_response(tasks)

    with _make_cn(handler) as cn:
        result = cn.tasks_list()
    assert result == tasks


def test_tasks_list_filters_status():
    captured = {}

    def handler(request):
        captured["params"] = dict(request.url.params)
        return _json_response([])

    with _make_cn(handler) as cn:
        cn.tasks_list(status="open")

    assert captured["params"].get("status") == "open"


# ──────────────────────────────────────────────────────────────────────────
# AgentNetwork.balance
# ──────────────────────────────────────────────────────────────────────────


def test_balance():
    def handler(request):
        return _json_response({"balance": 5000, "currency": "shells"})

    with _make_cn(handler) as cn:
        result = cn.balance()
    assert result["balance"] == 5000


# ──────────────────────────────────────────────────────────────────────────
# AgentNetwork.transfer
# ──────────────────────────────────────────────────────────────────────────


def test_transfer_sends_correct_payload():
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return _json_response({"sender_event": True})

    with _make_cn(handler) as cn:
        cn.transfer(from_did="did:a", to_did="did:b", amount=100, reason="seed")

    body = captured["body"]
    assert body["from"] == "did:a"
    assert body["to"] == "did:b"
    assert body["amount"] == 100


# ──────────────────────────────────────────────────────────────────────────
# AgentNetwork.peers
# ──────────────────────────────────────────────────────────────────────────


def test_peers_returns_list():
    peers = [{"peer_id": "12D3KooW…"}]

    def handler(request):
        return _json_response(peers)

    with _make_cn(handler) as cn:
        result = cn.peers()
    assert result == peers


# ──────────────────────────────────────────────────────────────────────────
# Lifecycle verbs
# ──────────────────────────────────────────────────────────────────────────


def _make_lifecycle(handler) -> Lifecycle:
    lc = Lifecycle.__new__(Lifecycle)
    lc._por = {}
    transport = httpx.MockTransport(handler)
    from anet._client import AgentNetwork as _CN
    inner = _CN.__new__(_CN)
    inner._base = "http://127.0.0.1:3998"
    inner._token = "testtoken"
    inner._client = httpx.Client(
        base_url="http://127.0.0.1:3998",
        transport=transport,
        headers={"Authorization": "Bearer testtoken"},
    )
    lc._cn = inner
    return lc


def test_lifecycle_claim():
    def handler(request):
        assert "/tasks/t1/claim" in request.url.path
        return _json_response({"ok": True})

    lc = _make_lifecycle(handler)
    result = lc.claim("t1")
    assert result == {"ok": True}


def test_lifecycle_evidence_post_stashes_por():
    def handler(request):
        return _json_response({"por_cid": "bafyabc123"})

    lc = _make_lifecycle(handler)
    lc.evidence_post("t1", description="test evidence")
    assert lc._por.get("t1") == "bafyabc123"


def test_lifecycle_submit_uses_stashed_por():
    captured = {}

    def handler(request):
        if "/evidence" in request.url.path:
            return _json_response({"por_cid": "bafyabc"})
        if "/submit" in request.url.path:
            captured["body"] = json.loads(request.content) if request.content else {}
            return _json_response({"ok": True})
        return _json_response({})

    lc = _make_lifecycle(handler)
    lc.evidence_post("t1", description="found it")
    lc.submit("t1")
    # por_cid should be auto-passed
    assert captured.get("body", {}).get("por_cid") == "bafyabc"


def test_lifecycle_accept():
    def handler(request):
        assert "/tasks/t1/accept" in request.url.path
        return _json_response({"ok": True})

    lc = _make_lifecycle(handler)
    result = lc.accept("t1")
    assert result == {"ok": True}


def test_lifecycle_context_manager():
    lc = _make_lifecycle(lambda r: _json_response({}))
    with lc as l2:
        assert l2 is lc
    # Should not raise after close
