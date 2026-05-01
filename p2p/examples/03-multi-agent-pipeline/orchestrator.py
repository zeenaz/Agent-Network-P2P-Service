"""03 — Orchestrator: fan-out to two workers and aggregate their results.

Architecture::

    caller
      │
      ▼
    orchestrator  (/process endpoint)
      ├─► worker-a  (/transform)  — uppercase the text
      └─► worker-b  (/sentiment)  — fake sentiment analysis

The orchestrator is itself a registered P2P service so it can be called from
any other peer on the mesh. Workers are also registered, so the orchestrator
discovers them by skill tag rather than hardcoding addresses.

Run::

    python orchestrator.py
"""

import json
import os
import sys
import time
from typing import Optional

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from anet.svc import AuthMissingError, SvcClient

PORT = int(os.environ.get("ORCH_PORT", "7310"))
BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
NAME = os.environ.get("ORCH_SVC_NAME", "orchestrator")

app = FastAPI(title=NAME)

# Shared SvcClient — created once at startup and closed at shutdown.
_svc: SvcClient | None = None


@app.on_event("startup")
def startup() -> None:
    global _svc  # noqa: PLW0603
    try:
        _svc = SvcClient(base_url=BASE_URL)
        _svc.register(
            name=NAME,
            endpoint=f"http://127.0.0.1:{PORT}",
            paths=["/process", "/health", "/meta"],
            modes=["rr"],
            free=True,
            tags=["orchestrator", "pipeline"],
            description="Multi-agent pipeline orchestrator",
            health_check="/health",
            meta_path="/meta",
        )
        print(f"[orch] ✓ registered {NAME}", flush=True)
    except AuthMissingError as e:
        print(f"[orch] auth error: {e}", file=sys.stderr)
        sys.exit(1)


@app.on_event("shutdown")
def shutdown() -> None:
    if _svc:
        try:
            _svc.unregister(NAME)
        except Exception:  # noqa: BLE001
            pass
        _svc.close()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": NAME}


@app.get("/meta")
def meta() -> dict:
    return {
        "name": NAME,
        "version": "0.1.0",
        "description": "Multi-agent pipeline orchestrator",
        "endpoints": [
            {"method": "POST", "path": "/process",
             "in": {"text": "string"},
             "out": {"transformed": "string", "sentiment": "string", "caller_did": "string"}},
        ],
    }


@app.post("/process")
async def process(
    req: Request,
    x_agent_did: Optional[str] = Header(default=None, convert_underscores=True),
) -> JSONResponse:
    """Fan out to worker-a (transform) and worker-b (sentiment), aggregate."""
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    text = body.get("text", "")

    if _svc is None:
        return JSONResponse({"error": "svc not initialised"}, status_code=503)

    # Discover workers.
    def discover_first(skill: str) -> tuple[str, str] | None:
        for _ in range(10):
            peers = _svc.discover(skill=skill)  # type: ignore[union-attr]
            if peers:
                p = peers[0]
                return p["peer_id"], p["services"][0]["name"]
            time.sleep(0.5)
        return None

    wa = discover_first("transform")
    wb = discover_first("sentiment")

    if not wa:
        return JSONResponse({"error": "no transform worker found"}, status_code=503)
    if not wb:
        return JSONResponse({"error": "no sentiment worker found"}, status_code=503)

    # Fan out (sequential for simplicity; parallelise with threads if needed).
    r_transform = _svc.call(wa[0], wa[1], "/transform",
                            method="POST", body={"text": text})
    r_sentiment = _svc.call(wb[0], wb[1], "/sentiment",
                            method="POST", body={"text": text})

    return JSONResponse({
        "transformed": (r_transform.get("body") or {}).get("result", ""),
        "sentiment": (r_sentiment.get("body") or {}).get("label", ""),
        "caller_did": x_agent_did,
    })


if __name__ == "__main__":
    import uvicorn
    print(f"[orch] starting on 127.0.0.1:{PORT}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
