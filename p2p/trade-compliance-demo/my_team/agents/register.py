"""Shared register helper for multi-agent pipeline."""

import os
import time
from typing import Optional

import httpx
from anet.svc import SvcAPIError, SvcClient


def register_agent(name: str, port: int, *, paths: list[str], tags: list[str],
                   description: str, per_call: int = 0,
                   base_url: Optional[str] = None) -> None:
    base_url = base_url or os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
    for _ in range(30):
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    else:
        print(f"[{name}] backend on :{port} never came up")
        raise SystemExit(1)

    with SvcClient(base_url=base_url) as svc:
        try:
            svc.unregister(name)
        except Exception:
            pass
        try:
            resp = svc.register(
                name=name,
                endpoint=f"http://127.0.0.1:{port}",
                paths=paths,
                modes=["rr"],
                per_call=per_call if per_call > 0 else None,
                free=per_call <= 0,
                tags=tags,
                description=description,
                health_check="/health",
                meta_path="/meta",
            )
        except SvcAPIError as e:
            print(f"[{name}] register failed: {e}")
            raise

    ans = resp.get("ans") or {}
    print(f"[{name}] ✓ registered (per_call={per_call}, published={ans.get('published')})")
