"""Tests for anet.svc module.

These tests use httpx's mock transport so they run without a live daemon.
"""

from __future__ import annotations

import json

import httpx
import pytest

from anet.svc import (
    AuthMissingError,
    SvcAPIError,
    SvcClient,
    SvcError,
    SSEEvent,
    _build_cost_model,
    _norm_paths,
    _resolve_token,
)


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _make_client(handler) -> SvcClient:
    """Return a SvcClient backed by a mock transport."""
    transport = httpx.MockTransport(handler)
    inner = httpx.Client(
        base_url="http://127.0.0.1:3998",
        transport=transport,
        headers={"Authorization": "Bearer testtoken"},
    )
    return SvcClient(token="testtoken", client=inner)


def _json_response(body: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status,
        headers={"Content-Type": "application/json"},
        content=json.dumps(body).encode(),
    )


# ──────────────────────────────────────────────────────────────────────────
# _resolve_token
# ──────────────────────────────────────────────────────────────────────────


def test_resolve_token_explicit():
    assert _resolve_token("explicit") == "explicit"


def test_resolve_token_env(monkeypatch):
    monkeypatch.setenv("ANET_TOKEN", "envtok")
    monkeypatch.delenv("ANET_TOKEN", raising=False)
    # Explicit takes precedence
    assert _resolve_token("explicit") == "explicit"


def test_resolve_token_from_env(monkeypatch):
    monkeypatch.setenv("ANET_TOKEN", "from_env")
    assert _resolve_token(None) == "from_env"


def test_resolve_token_none(monkeypatch, tmp_path):
    monkeypatch.delenv("ANET_TOKEN", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    # No token file ⟹ None
    assert _resolve_token(None) is None


def test_resolve_token_file(monkeypatch, tmp_path):
    monkeypatch.delenv("ANET_TOKEN", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    anet_dir = tmp_path / ".anet"
    anet_dir.mkdir()
    (anet_dir / "api_token").write_text("filetok\n")
    assert _resolve_token(None) == "filetok"


# ──────────────────────────────────────────────────────────────────────────
# _norm_paths
# ──────────────────────────────────────────────────────────────────────────


def test_norm_paths_strings():
    assert _norm_paths(["/echo", "/health"]) == [
        {"prefix": "/echo"},
        {"prefix": "/health"},
    ]


def test_norm_paths_dicts():
    inp = [{"prefix": "/echo", "methods": ["POST"]}]
    assert _norm_paths(inp) == inp


def test_norm_paths_invalid():
    with pytest.raises(SvcError):
        _norm_paths([123])


# ──────────────────────────────────────────────────────────────────────────
# _build_cost_model
# ──────────────────────────────────────────────────────────────────────────


def test_cost_model_free():
    assert _build_cost_model(
        free=True, per_call=None, per_kb=None, per_minute=None,
        deposit=None, override=None,
    ) == {"free": True}


def test_cost_model_per_call():
    cm = _build_cost_model(
        free=False, per_call=10, per_kb=None, per_minute=None,
        deposit=None, override=None,
    )
    assert cm == {"per_call": 10}


def test_cost_model_override():
    override = {"custom": True}
    cm = _build_cost_model(
        free=True, per_call=5, per_kb=None, per_minute=None,
        deposit=None, override=override,
    )
    assert cm == {"custom": True}


def test_cost_model_none_when_no_fields():
    cm = _build_cost_model(
        free=False, per_call=None, per_kb=None, per_minute=None,
        deposit=None, override=None,
    )
    assert cm is None


# ──────────────────────────────────────────────────────────────────────────
# AuthMissingError
# ──────────────────────────────────────────────────────────────────────────


def test_auth_missing_error(monkeypatch, tmp_path):
    monkeypatch.delenv("ANET_TOKEN", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(AuthMissingError):
        SvcClient()


# ──────────────────────────────────────────────────────────────────────────
# SvcClient.list
# ──────────────────────────────────────────────────────────────────────────


def test_list_returns_services():
    services = [{"name": "echo", "endpoint": "http://127.0.0.1:7100"}]

    def handler(request):
        return _json_response(services)

    with _make_client(handler) as svc:
        result = svc.list()
    assert result == services


def test_list_returns_empty_on_null():
    def handler(request):
        return _json_response(None)  # type: ignore[arg-type]

    with _make_client(handler) as svc:
        result = svc.list()
    assert result == []


# ──────────────────────────────────────────────────────────────────────────
# SvcClient.register
# ──────────────────────────────────────────────────────────────────────────


def test_register_sends_correct_payload():
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return _json_response({"name": "echo", "ans": {}})

    with _make_client(handler) as svc:
        svc.register(
            name="echo",
            endpoint="http://127.0.0.1:7100",
            paths=["/echo"],
            free=True,
            tags=["demo"],
        )

    body = captured["body"]
    assert body["name"] == "echo"
    assert body["endpoint"] == "http://127.0.0.1:7100"
    assert body["cost_model"] == {"free": True}
    assert body["tags"] == ["demo"]
    assert body["paths"] == [{"prefix": "/echo"}]


def test_register_raises_on_error():
    def handler(request):
        return _json_response(
            {"errors": ["name is required", "endpoint is required"]},
            status=400,
        )

    with _make_client(handler) as svc:
        with pytest.raises(SvcAPIError) as exc_info:
            svc.register(
                name="",
                endpoint="",
                paths=[],
                free=True,
            )
    assert exc_info.value.status == 400
    assert "name is required" in exc_info.value.errors


# ──────────────────────────────────────────────────────────────────────────
# SvcClient.discover
# ──────────────────────────────────────────────────────────────────────────


def test_discover_requires_peer_or_skill():
    with _make_client(lambda r: _json_response({})) as svc:
        with pytest.raises(SvcError, match="requires peer_id= or skill="):
            svc.discover()


def test_discover_by_skill_returns_results():
    payload = {"results": [{"peer_id": "abc", "services": []}]}

    def handler(request):
        return _json_response(payload)

    with _make_client(handler) as svc:
        result = svc.discover(skill="echo")
    assert result == [{"peer_id": "abc", "services": []}]


def test_discover_by_peer_id():
    payload = {"peer_id": "abc", "services": []}

    def handler(request):
        return _json_response(payload)

    with _make_client(handler) as svc:
        result = svc.discover(peer_id="abc")
    assert result == payload


# ──────────────────────────────────────────────────────────────────────────
# SvcClient.call
# ──────────────────────────────────────────────────────────────────────────


def test_call_sends_correct_payload():
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return _json_response({"status": 200, "body": {"echo": "hi"}})

    with _make_client(handler) as svc:
        resp = svc.call("peer1", "echo-svc", "/echo",
                        method="POST", body={"hi": 1})

    assert resp["status"] == 200
    body = captured["body"]
    assert body["peer_id"] == "peer1"
    assert body["service"] == "echo-svc"
    assert body["path"] == "/echo"
    assert body["body"] == {"hi": 1}


def test_call_raises_svc_api_error():
    def handler(request):
        return _json_response({"message": "peer not found"}, status=404)

    with _make_client(handler) as svc:
        with pytest.raises(SvcAPIError) as exc_info:
            svc.call("badpeer", "echo", "/echo")
    assert exc_info.value.status == 404


# ──────────────────────────────────────────────────────────────────────────
# SvcClient.audit
# ──────────────────────────────────────────────────────────────────────────


def test_audit_extracts_calls_key():
    rows = [{"service": "echo", "status": 200, "cost": 0}]

    def handler(request):
        return _json_response({"calls": rows})

    with _make_client(handler) as svc:
        result = svc.audit(limit=1)
    assert result == rows


def test_audit_handles_plain_list():
    rows = [{"service": "echo", "status": 200}]

    def handler(request):
        return _json_response(rows)

    with _make_client(handler) as svc:
        result = svc.audit()
    assert result == rows


# ──────────────────────────────────────────────────────────────────────────
# SvcClient._encode_body
# ──────────────────────────────────────────────────────────────────────────


def test_encode_body_dict():
    assert SvcClient._encode_body({"a": 1}) == {"a": 1}


def test_encode_body_bytes_json():
    assert SvcClient._encode_body(b'{"x": 1}') == {"x": 1}


def test_encode_body_str_json():
    assert SvcClient._encode_body('{"y": 2}') == {"y": 2}


def test_encode_body_plain_str():
    assert SvcClient._encode_body("hello") == "hello"


def test_encode_body_none():
    assert SvcClient._encode_body(None) is None


def test_encode_body_invalid_type():
    with pytest.raises(SvcError):
        SvcClient._encode_body(object())  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────────────
# SSEEvent
# ──────────────────────────────────────────────────────────────────────────


def test_sse_event_is_terminal():
    assert SSEEvent(event="done", data="end").is_terminal is True
    assert SSEEvent(event="error", data="oops").is_terminal is True
    assert SSEEvent(event="message", data="hi").is_terminal is False


# ──────────────────────────────────────────────────────────────────────────
# SvcClient.show
# ──────────────────────────────────────────────────────────────────────────


def test_show_finds_service():
    services = [{"name": "echo"}, {"name": "llm"}]

    def handler(request):
        return _json_response(services)

    with _make_client(handler) as svc:
        result = svc.show("echo")
    assert result == {"name": "echo"}


def test_show_raises_when_not_found():
    def handler(request):
        return _json_response([{"name": "other"}])

    with _make_client(handler) as svc:
        with pytest.raises(SvcError, match="not found"):
            svc.show("echo")
