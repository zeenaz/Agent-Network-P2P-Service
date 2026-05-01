"""Register the LLM service with the local anet daemon.

Uses per-call billing: 10 micro-credits per ``/generate`` call.
The ``/stream`` path is also registered in ``server-stream`` mode.

Run AFTER ``llm_backend.py`` is healthy.
"""

import os
import sys
import time

import httpx

from anet.svc import SvcClient

BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
LLM_PORT = int(os.environ.get("LLM_PORT", "7200"))
NAME = os.environ.get("LLM_SVC_NAME", "llm-svc")
PER_CALL = int(os.environ.get("LLM_PER_CALL", "10"))


def wait_for_backend(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=2.0)
            if r.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise RuntimeError(f"LLM backend on :{port} not reachable after {timeout}s")


def main() -> int:
    print(f"[service] waiting for LLM backend on :{LLM_PORT} …", flush=True)
    wait_for_backend(LLM_PORT)
    print("[service] backend healthy", flush=True)

    with SvcClient(base_url=BASE_URL) as svc:
        try:
            svc.unregister(NAME)
        except Exception:  # noqa: BLE001
            pass

        resp = svc.register(
            name=NAME,
            endpoint=f"http://127.0.0.1:{LLM_PORT}",
            paths=["/generate", "/stream", "/health", "/meta"],
            modes=["rr", "server-stream"],
            per_call=PER_CALL,
            deposit=50,
            tags=["llm", "generate", "stream"],
            description=f"LLM-as-a-service (per_call={PER_CALL} credits)",
            health_check="/health",
            meta_path="/meta",
        )
        ans = resp.get("ans") or {}
        print(
            f"[service] ✓ registered {NAME} "
            f"ans.published={ans.get('published')} uri={ans.get('uri')}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
