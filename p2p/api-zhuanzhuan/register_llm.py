"""把 bank 注册到本机 anet daemon（daemon-1）。

依赖环境变量：
  ANET_BASE_URL   默认 http://127.0.0.1:13921
  BANK_PORT       默认 7200
  BANK_SVC_NAME   默认 api-zhuanzhuan-bank
"""
import os
import sys
from pathlib import Path

from anet.svc import SvcClient


def _read_default_token() -> str:
    for p in ("/tmp/anet-p2p-u1/.anet/api_token", os.path.expanduser("~/.anet/api_token")):
        if Path(p).exists():
            return Path(p).read_text().strip()
    return ""


NAME = os.environ.get("BANK_SVC_NAME", "api-zhuanzhuan-bank")
PORT = os.environ.get("BANK_PORT", "7200")
ANET_BASE = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
ANET_TOKEN = os.environ.get("ANET_TOKEN") or _read_default_token()


def main() -> int:
    with SvcClient(ANET_BASE, ANET_TOKEN) as svc:
        try:
            svc.unregister(NAME)
        except Exception:
            pass
        # 清理旧服务名
        for old in ("claude-relay",):
            try:
                svc.unregister(old)
            except Exception:
                pass

        resp = svc.register(
            name=NAME,
            endpoint=f"http://127.0.0.1:{PORT}",
            paths=["/deposit", "/lease", "/audit", "/deposits", "/health", "/meta"],
            modes=["rr"],
            free=True,
            tags=["key-bank", "p2p", "api-zhuanzhuan", "deposit-lease"],
            description="API 转转 bank: A deposit key, B lease key (one-time, no upstream verification). Based on AgentNetwork.",
            health_check="/health",
            meta_path="/meta",
        )
        print(f"✓ registered {resp.get('name')} ans={resp.get('ans')}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
