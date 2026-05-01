"""ex03 — Consume a server-stream from a remote service.

Run::

    python -m anet.examples.ex03_stream_consume

What it does:
1. Discovers all peers exposing the ``echo`` skill.
2. Opens a streaming connection to the first peer's ``/stream`` endpoint.
3. Prints each SSE frame until the stream terminates.

Prerequisites:
- ``anet daemon &`` must be running.
- A peer must expose a streaming endpoint (e.g. the starter-template backend
  which ships a ``POST /stream`` route that emits 5 JSON chunks).
- ``$ANET_BASE_URL`` and ``$ANET_TOKEN`` (or ``~/.anet/api_token``) set.
"""

from __future__ import annotations

import os
import sys
import time

from anet.svc import AuthMissingError, SvcAPIError, SvcClient

BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:3998")
SKILL = os.environ.get("TARGET_SKILL", "echo")
STREAM_PATH = os.environ.get("STREAM_PATH", "/stream")


def main() -> int:
    try:
        svc = SvcClient(base_url=BASE_URL, timeout=None)
    except AuthMissingError as e:
        print(f"[ex03] {e}", file=sys.stderr)
        return 1

    with svc:
        print(f"[ex03] discovering skill={SKILL!r} …", flush=True)
        peers = []
        for _ in range(15):
            peers = svc.discover(skill=SKILL)
            if peers:
                break
            time.sleep(1)

        if not peers:
            print(f"[ex03] no peers expose skill={SKILL!r}", file=sys.stderr)
            return 1

        target = peers[0]
        peer_id = target["peer_id"]
        svc_name = target["services"][0]["name"]

        print(
            f"[ex03] opening stream to {svc_name} on "
            f"{peer_id[:20]}… {STREAM_PATH}",
            flush=True,
        )
        try:
            for ev in svc.stream(
                peer_id,
                svc_name,
                STREAM_PATH,
                method="POST",
                body={"prompt": "give me 5 ticks"},
                mode="server-stream",
            ):
                print(f"  [{ev.event}] {ev.data}")
                if ev.is_terminal:
                    break
        except SvcAPIError as e:
            print(f"[ex03] stream failed: {e}", file=sys.stderr)
            return 1

    print("[ex03] stream complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
