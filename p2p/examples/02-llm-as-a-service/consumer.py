"""02 consumer — discover the LLM service and run a completion.

Demonstrates:
- Discovering a service by skill tag (``llm``).
- Making a priced call (credits are deducted automatically).
- Streaming token output.

Usage::

    python consumer.py              # request/response
    python consumer.py --stream     # streaming
"""

import argparse
import os
import sys
import time

from anet.svc import AuthMissingError, SvcAPIError, SvcClient

BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13922")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM service consumer")
    p.add_argument("--stream", action="store_true", help="use server-stream mode")
    p.add_argument(
        "--prompt",
        default="Write a haiku about distributed systems.",
        help="prompt to send",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    try:
        svc = SvcClient(base_url=BASE_URL)
    except AuthMissingError as e:
        print(f"[consumer] {e}", file=sys.stderr)
        return 1

    with svc:
        print("[consumer] discovering llm skill …", flush=True)
        peers = []
        for _ in range(15):
            peers = svc.discover(skill="llm")
            if peers:
                break
            time.sleep(1)

        if not peers:
            print("[consumer] no peers expose skill=llm", file=sys.stderr)
            return 1

        target = peers[0]
        peer_id = target["peer_id"]
        svc_name = target["services"][0]["name"]
        print(f"[consumer] found {svc_name} on {peer_id[:18]}…")

        if args.stream:
            print(f"[consumer] streaming /stream — prompt: {args.prompt!r}\n")
            try:
                for ev in svc.stream(
                    peer_id,
                    svc_name,
                    "/stream",
                    method="POST",
                    body={"prompt": args.prompt},
                    mode="server-stream",
                ):
                    if ev.event == "message" and ev.data:
                        try:
                            import json
                            tok = json.loads(ev.data).get("token", "")
                            print(tok, end="", flush=True)
                        except Exception:  # noqa: BLE001
                            print(ev.data, end="", flush=True)
                    if ev.is_terminal:
                        break
                print()  # newline after streaming output
            except SvcAPIError as e:
                print(f"\n[consumer] stream failed: {e}", file=sys.stderr)
                return 1
        else:
            print(f"[consumer] calling /generate — prompt: {args.prompt!r}")
            try:
                resp = svc.call(
                    peer_id,
                    svc_name,
                    "/generate",
                    method="POST",
                    body={"prompt": args.prompt, "max_tokens": 128},
                )
            except SvcAPIError as e:
                print(f"[consumer] call failed: {e}", file=sys.stderr)
                return 1
            print(f"[consumer] HTTP {resp.get('status')}")
            body = resp.get("body") or {}
            print(f"  text:       {body.get('text', '')}")
            print(f"  caller_did: {body.get('caller_did', '')}")

        # Print audit row so we can verify billing.
        rows = svc.audit(limit=1)
        if rows:
            r = rows[0]
            print(
                f"\n[consumer] audit: {r['service']}  {r['method']} {r['path']}"
                f"  status={r['status']}  cost={r['cost']} credits"
                f"  duration={r['duration_ms']}ms"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
