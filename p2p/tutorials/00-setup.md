---
title: "Setup — Install anet and boot your first two nodes"
description: "Everything you need before you can register a service or make a cross-node call."
---

# 00 — Setup / 环境搭建

## 1. 你将完成什么 / What you'll achieve

By the end of this tutorial you will have:

- The `anet` binary installed and verified.
- A Python virtualenv with `anet-sdk` (and FastAPI for examples).
- Two isolated daemon instances running on your laptop, connected to each
  other via a local libp2p mesh.

## 2. Prerequisites / 前置条件

- macOS or Linux (Windows: use WSL 2).
- Python ≥ 3.9.
- `curl` available on `$PATH`.
- Git (to clone this repo).

## 3. Steps / 步骤

### 3.1 Install the anet daemon / 安装 anet daemon

```bash
curl -fsSL https://agentnetwork.org.cn/install.sh | sh
anet --version   # should print anet v1.1.x
```

The install script places the `anet` binary in `~/.anet/bin` and adds it to
your shell profile. Open a new terminal if the command is not found.

### 3.2 Install the Python SDK / 安装 Python SDK

```bash
cd /path/to/Agent-Network-P2P-Service
python -m venv .venv && source .venv/bin/activate
pip install -e sdk/python        # editable install of this repo's SDK
pip install fastapi uvicorn httpx python-dotenv  # for examples
```

Or install from PyPI:

```bash
pip install anet-sdk fastapi uvicorn httpx python-dotenv
```

### 3.3 Boot two local daemons / 起两个本地 daemon

```bash
bash p2p/starter-template/scripts/two-node.sh start
```

Expected output (last few lines):

```
✓ daemon-1   API=http://127.0.0.1:13921   HOME=/tmp/anet-p2p-u1
✓ daemon-2   API=http://127.0.0.1:13922   HOME=/tmp/anet-p2p-u2
✓ seed transfers ok (1000⇄1000 shells)
```

Leave this terminal open. The daemons are running in the background.

### 3.4 Verify / 验证

Open **another** terminal:

```bash
# daemon-1
curl -s http://127.0.0.1:13921/api/status | python3 -m json.tool

# daemon-2
curl -s http://127.0.0.1:13922/api/status | python3 -m json.tool
```

Both should return a JSON object with `"peer_id"`, `"did"`, and `"peers": 1`.

## 4. Sanity checklist / 自检命令

```bash
# A. anet binary works
anet --version

# B. SDK importable
python -c "from anet.svc import SvcClient; print('SDK OK')"

# C. Both daemons alive
curl -sf http://127.0.0.1:13921/api/status >/dev/null && echo "daemon-1 OK"
curl -sf http://127.0.0.1:13922/api/status >/dev/null && echo "daemon-2 OK"
```

## 5. Troubleshooting / 故障对照

| Symptom | Cause | Fix |
|---|---|---|
| `anet: command not found` | Binary not in PATH | `export PATH="$HOME/.anet/bin:$PATH"` |
| `curl: (7) Failed to connect` on port 13921 | daemon-1 not started | Re-run `two-node.sh start` |
| `peers: 0` on both daemons | libp2p handshake pending | Wait 5 s and re-check |
| `ModuleNotFoundError: No module named 'anet'` | venv not activated | `source .venv/bin/activate` |

Next → [01-first-service.md](01-first-service.md)
