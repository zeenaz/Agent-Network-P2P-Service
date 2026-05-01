"""ex01 — Register a local HTTP service on the AgentNetwork mesh.

Run::

    python -m anet.examples.ex01_register_local_service

What it does:
1. Starts a tiny stdlib HTTP echo server on localhost:7901.
2. Registers it with the local anet daemon as "demo-echo-<hash>".
3. Prints the registration result (name, ANS URI).
4. Waits for Ctrl-C, then unregisters cleanly.

Prerequisites:
- ``anet daemon &`` must be running (default port 3998).
- ``$ANET_TOKEN`` or ``~/.anet/api_token`` must hold the bearer token.
"""

from __future__ import annotations

import http.server
import json
import os
import signal
import socket
import sys
import threading

from anet.svc import AuthMissingError, SvcClient

PORT = int(os.environ.get("DEMO_PORT", "7901"))
BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:3998")


# ──────────────────────────────────────────────────────────────────────────
# Tiny echo backend (stdlib only)
# ──────────────────────────────────────────────────────────────────────────


class _Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, status: int, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/meta"):
            body = json.dumps({
                "name": "demo-echo",
                "version": "1.0.0",
                "endpoints": [{"method": "POST", "path": "/echo"}],
            }).encode()
        else:
            body = b'{"ok": true}'
        self._send(200, body)

    def do_POST(self) -> None:  # noqa: N802
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) if n else b"{}"
        did = self.headers.get("X-Agent-DID", "<missing>")
        try:
            payload = json.loads(raw)
        except Exception:  # noqa: BLE001
            payload = raw.decode("utf-8", "replace")
        self._send(200, json.dumps({"echo": payload, "caller_did": did}).encode())

    def log_message(self, *_: object) -> None:
        return


def _short_hash() -> str:
    import hashlib
    return hashlib.sha256(socket.gethostname().encode()).hexdigest()[:6]


# ──────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    name = f"demo-echo-{_short_hash()}"

    # Start the echo server in a background thread.
    server = http.server.HTTPServer(("127.0.0.1", PORT), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[ex01] echo backend listening on 127.0.0.1:{PORT}", flush=True)

    try:
        svc = SvcClient(base_url=BASE_URL)
    except AuthMissingError as e:
        print(f"[ex01] {e}", file=sys.stderr)
        return 1

    try:
        resp = svc.register(
            name=name,
            endpoint=f"http://127.0.0.1:{PORT}",
            paths=["/echo", "/health", "/meta"],
            modes=["rr"],
            free=True,
            tags=["demo", "echo"],
            description="ex01 demo echo service",
            health_check="/health",
            meta_path="/meta",
        )
        ans = resp.get("ans") or {}
        print(
            f"[ex01] ✓ registered name={name} "
            f"ans.published={ans.get('published')} uri={ans.get('uri')}",
            flush=True,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[ex01] register failed: {e}", file=sys.stderr)
        svc.close()
        return 1

    print("[ex01] service is live — press Ctrl-C to unregister and exit")

    def _shutdown(*_: object) -> None:
        print("\n[ex01] unregistering …", flush=True)
        try:
            svc.unregister(name)
        except Exception as exc:  # noqa: BLE001
            print(f"[ex01] unregister failed (non-fatal): {exc}", file=sys.stderr)
        svc.close()
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Block until signal.
    signal.pause()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
