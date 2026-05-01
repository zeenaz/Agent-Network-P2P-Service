"""ex02 — Discover a peer by skill and call its service.

Run::

    python -m anet.examples.ex02_discover_and_call

What it does:
1. Discovers all peers that expose the ``echo`` skill via ANS.
2. Picks the first peer and calls its ``/echo`` endpoint.
3. Prints the response body and the latest audit row.

Prerequisites:
- ``anet daemon &`` must be running.
- At least one peer on the mesh must have the ``echo`` skill registered
  (e.g. run ex01 on a different daemon or laptop on the same network).
- ``$ANET_BASE_URL`` and ``$ANET_TOKEN`` (or ``~/.anet/api_token``) set.
"""

from __future__ import annotations

import os
import sys
import time

from anet.svc import AuthMissingError, SvcAPIError, SvcClient

BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:3998")
SKILL = os.environ.get("TARGET_SKILL", "echo")


def main() -> int:
    try:
        svc = SvcClient(base_url=BASE_URL)
    except AuthMissingError as e:
        print(f"[ex02] {e}", file=sys.stderr)
        return 1

    with svc:
        # ANS gossip needs a moment to converge after a fresh register.
        print(f"[ex02] discovering skill={SKILL!r} …", flush=True)
        peers = []
        for _ in range(15):
            peers = svc.discover(skill=SKILL)
            if peers:
                break
            time.sleep(1)

        if not peers:
            print(f"[ex02] no peers expose skill={SKILL!r}", file=sys.stderr)
            return 1

        print(f"[ex02] found {len(peers)} peer(s):")
        for p in peers:
            svcs = ", ".join(s["name"] for s in p["services"])
            print(f"  - {p['peer_id'][:20]}…  services=[{svcs}]")

        target = peers[0]
        peer_id = target["peer_id"]
        svc_name = target["services"][0]["name"]

        print(f"\n[ex02] calling {svc_name} on {peer_id[:20]}… /echo", flush=True)
        try:
            resp = svc.call(
                peer_id,
                svc_name,
                "/echo",
                method="POST",
                body={"msg": "hello from ex02"},
            )
        except SvcAPIError as e:
            print(f"[ex02] call failed: {e}", file=sys.stderr)
            return 1

        print(f"[ex02] HTTP {resp.get('status')}  body={resp.get('body')}")

        rows = svc.audit(limit=1)
        if rows:
            r = rows[0]
            print(
                f"\n[ex02] audit: {r['service']}  {r['method']} {r['path']}"
                f"  status={r['status']}  cost={r['cost']}  "
                f"duration={r['duration_ms']}ms"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
