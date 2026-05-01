"""02 — LLM backend (Ollama or fake-stub for testing).

Exposes two endpoints:
  POST /generate   — request/response completion
  POST /stream     — server-stream token-by-token output

Set ``LLM_BACKEND=fake`` (default) to use the deterministic stub; set
``LLM_BACKEND=ollama`` to proxy to a local Ollama instance.

Run::

    python llm_backend.py
"""

import json
import os
import sys
import time
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse

PORT = int(os.environ.get("LLM_PORT", "7200"))
BACKEND = os.environ.get("LLM_BACKEND", "fake").lower()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

app = FastAPI(title="llm-svc")


def _fake_complete(prompt: str, max_tokens: int = 64) -> str:
    """Deterministic stub — useful when no Ollama is available."""
    words = ["Hello", "world", "this", "is", "a", "fake", "LLM", "response", "to"]
    words += prompt.split()[:5]
    return " ".join(words[:max_tokens])


def _ollama_complete(prompt: str, max_tokens: int = 64) -> str:
    import httpx
    resp = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False,
              "options": {"num_predict": max_tokens}},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def _fake_stream(prompt: str):
    tokens = _fake_complete(prompt).split()
    for tok in tokens:
        time.sleep(0.05)
        yield json.dumps({"token": tok}) + "\n"


def _ollama_stream(prompt: str):
    import httpx
    with httpx.stream(
        "POST",
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": True},
        timeout=None,
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    yield json.dumps({"token": chunk.get("response", "")}) + "\n"
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue


@app.get("/health")
def health() -> dict:
    return {"ok": True, "backend": BACKEND, "model": MODEL if BACKEND == "ollama" else "fake"}


@app.get("/meta")
def meta() -> dict:
    return {
        "name": "llm-svc",
        "version": "0.1.0",
        "description": f"LLM-as-a-service ({BACKEND})",
        "endpoints": [
            {"method": "POST", "path": "/generate",
             "in": {"prompt": "string", "max_tokens": "int"},
             "out": {"text": "string", "caller_did": "string"}},
            {"method": "POST", "path": "/stream",
             "out": "newline-delimited JSON {token: string}"},
        ],
    }


@app.post("/generate")
async def generate(
    req: Request,
    x_agent_did: Optional[str] = Header(default=None, convert_underscores=True),
) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    prompt = body.get("prompt", "")
    max_tokens = int(body.get("max_tokens", 64))
    try:
        if BACKEND == "ollama":
            text = _ollama_complete(prompt, max_tokens)
        else:
            text = _fake_complete(prompt, max_tokens)
        return JSONResponse({"text": text, "caller_did": x_agent_did})
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "upstream backend error"}, status_code=502)


@app.post("/stream")
async def stream_endpoint(req: Request) -> StreamingResponse:
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        body = {}
    prompt = body.get("prompt", "Tell me something interesting.")
    gen = _ollama_stream(prompt) if BACKEND == "ollama" else _fake_stream(prompt)
    return StreamingResponse(gen, media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    print(f"[llm] starting on 127.0.0.1:{PORT} backend={BACKEND}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
