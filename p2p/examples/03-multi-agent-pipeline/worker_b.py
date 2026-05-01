"""03 — Worker B: fake sentiment analysis service.

Registers itself with the ``sentiment`` skill tag.

Run::

    python worker_b.py
"""

import os
import sys
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from anet.svc import AuthMissingError, SvcClient

PORT = int(os.environ.get("WORKER_B_PORT", "7312"))
BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
NAME = os.environ.get("WORKER_B_NAME", "worker-sentiment")

app = FastAPI(title=NAME)
_svc: SvcClient | None = None

_POSITIVE_WORDS = {"good", "great", "excellent", "love", "amazing", "wonderful", "fantastic"}
_NEGATIVE_WORDS = {"bad", "terrible", "awful", "hate", "horrible", "dreadful", "worst"}


def _classify(text: str) -> str:
    words = set(text.lower().split())
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


@app.on_event("startup")
def startup() -> None:
    global _svc  # noqa: PLW0603
    try:
        _svc = SvcClient(base_url=BASE_URL)
        _svc.register(
            name=NAME,
            endpoint=f"http://127.0.0.1:{PORT}",
            paths=["/sentiment", "/health", "/meta"],
            modes=["rr"],
            free=True,
            tags=["sentiment", "nlp", "worker"],
            description="Fake sentiment analysis worker",
            health_check="/health",
            meta_path="/meta",
        )
        print(f"[worker-b] ✓ registered {NAME}", flush=True)
    except AuthMissingError as e:
        print(f"[worker-b] auth error: {e}", file=sys.stderr)
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
        "description": "Fake sentiment analysis worker",
        "endpoints": [
            {"method": "POST", "path": "/sentiment",
             "in": {"text": "string"},
             "out": {"label": "positive|negative|neutral", "caller_did": "string"}},
        ],
    }


@app.post("/sentiment")
async def sentiment(
    req: Request,
    x_agent_did: Optional[str] = Header(default=None, convert_underscores=True),
) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    text = body.get("text", "")
    label = _classify(text)
    return JSONResponse({"label": label, "caller_did": x_agent_did})


if __name__ == "__main__":
    import uvicorn
    print(f"[worker-b] starting on 127.0.0.1:{PORT}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
