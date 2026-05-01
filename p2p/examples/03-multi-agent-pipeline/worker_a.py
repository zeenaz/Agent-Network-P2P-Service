"""03 — Worker A: text transform service (uppercase).

Registers itself with the ``transform`` skill tag so the orchestrator can
discover it by capability.

Run::

    python worker_a.py
"""

import os
import sys
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from anet.svc import AuthMissingError, SvcClient

PORT = int(os.environ.get("WORKER_A_PORT", "7311"))
BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
NAME = os.environ.get("WORKER_A_NAME", "worker-transform")

app = FastAPI(title=NAME)
_svc: SvcClient | None = None


@app.on_event("startup")
def startup() -> None:
    global _svc  # noqa: PLW0603
    try:
        _svc = SvcClient(base_url=BASE_URL)
        _svc.register(
            name=NAME,
            endpoint=f"http://127.0.0.1:{PORT}",
            paths=["/transform", "/health", "/meta"],
            modes=["rr"],
            free=True,
            tags=["transform", "worker"],
            description="Text transform worker (uppercase)",
            health_check="/health",
            meta_path="/meta",
        )
        print(f"[worker-a] ✓ registered {NAME}", flush=True)
    except AuthMissingError as e:
        print(f"[worker-a] auth error: {e}", file=sys.stderr)
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
        "description": "Text transform worker",
        "endpoints": [
            {"method": "POST", "path": "/transform",
             "in": {"text": "string"},
             "out": {"result": "string", "caller_did": "string"}},
        ],
    }


@app.post("/transform")
async def transform(
    req: Request,
    x_agent_did: Optional[str] = Header(default=None, convert_underscores=True),
) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    text = body.get("text", "")
    return JSONResponse({"result": text.upper(), "caller_did": x_agent_did})


if __name__ == "__main__":
    import uvicorn
    print(f"[worker-a] starting on 127.0.0.1:{PORT}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
