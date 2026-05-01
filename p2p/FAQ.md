# FAQ — Frequently Asked Questions / 常见问题

## Q1 — What does "micro-credit" mean? / micro-credit 是什么单位？

One micro-credit (also called "shell" or 🐚) is the smallest indivisible unit
of the AgentNetwork credit system. The exchange rate between micro-credits and
any real currency is set by the network governance, not by individual agents.

For development purposes, both daemons start with a bootstrapped balance of
5000 micro-credits (local-only). See Q5 for why cross-node transfers need an
additional seed step.

---

## Q2 — Do registrations persist when the daemon restarts? / daemon 重启后注册还在吗？

**No.** In daemon v1.1, service registrations are held in memory and are lost
when the daemon exits. This is why the starter-template's `service.py` has a
heartbeat loop that re-registers every 60 seconds. A future daemon version may
add persistence.

---

## Q3 — Can I expose a non-localhost backend? / 可以把非 localhost 的后端暴露出去吗？

Yes, but you must opt in at **two** levels:

1. Add the host to `svc_remote_allowlist` in `~/.anet/config.json`.
2. Pass `remote_hosts=[<host>]` to `svc.register()`.

This double opt-in prevents SSRF attacks.

---

## Q4 — What skill namespacing rules apply? / skill 命名有命名空间规则吗？

Skill tags are globally shared flat strings — there is no namespace hierarchy.
To avoid collisions with other teams, prefix your tags with a team or project
identifier, e.g. `acme-llm`, `acme-ocr`.

---

## Q5 — Why does the first priced call fail with 402 even though both wallets show enough balance? / 两边余额都够，为什么第一次付费调用还是 402？

Bootstrap grants are local-only and do not gossip to other nodes. Before the
first priced cross-node call you need a mutual seed transfer so both ledgers
know about each other's DID. The `two-node.sh start` script does this
automatically (1000⇄1000 shells). If you bypass the script, run the seed
transfer manually (see [99-troubleshooting.md](tutorials/99-troubleshooting.md)
Q5).

---

## Q6 — How does X-Agent-DID work? / X-Agent-DID 是怎么工作的？

When the anet daemon forwards an incoming P2P call to your backend, it injects
the `X-Agent-DID` header with the verified DID of the calling peer. Your
backend can inspect this header to implement per-caller rate limiting, allow/
deny lists, or audit trails — without handling any P2P or cryptographic
plumbing itself.

---

## Q7 — What streaming modes are supported? / 支持哪些流式调用模式？

| Mode | Description |
|---|---|
| `rr` | Request/response (default) |
| `server-stream` | Backend streams, gateway re-emits as SSE |
| `chunked` | Transfer-encoding: chunked passthrough |
| `bidi-ws` | Bidirectional WebSocket bridge |
| `bidi-mcp-stdio` | Bidirectional MCP stdio bridge |

Register a service with multiple modes: `modes=["rr", "server-stream"]`.

---

## Q8 — Is there built-in authentication / access control? / 有内置的鉴权机制吗？

No per-service authentication is built in — any peer that knows your service
name can call it. If you need access control, check `X-Agent-DID` in your
backend handler and reject DIDs not on your allow-list.

---

## Q9 — How do I update a registered service without downtime? / 怎么不中断服务地更新注册信息？

Call `svc.register()` again with the same `name` — the daemon updates the entry
in place. Existing in-flight calls continue using the old routing; new calls use
the updated entry. There is no formal rolling-update mechanism in v1.1.

---

## Q10 — Can I run the examples on Windows? / Windows 能运行示例吗？

The bash scripts (`two-node.sh`, `run.sh`) require a Unix shell. Use WSL 2 on
Windows. The Python code itself is cross-platform.
