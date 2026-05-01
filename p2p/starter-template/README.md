# my-agent — AgentNetwork P2P Starter

A working scaffold you can fork and turn into anything. Out of the box you get:

- A **FastAPI backend** (`my_agent/backend.py`) with `/echo`, `/health`,
  `/meta`, `/stream` so the gateway can do health probing, register-time meta
  probing, and server-stream demos.
- A **register loop** (`my_agent/service.py`) that waits for the backend,
  registers it with the local `anet` daemon, re-registers every 60 s in case
  the daemon restarted, and unregisters cleanly on Ctrl-C.
- A **discovery + call client** (`my_agent/client.py`) that finds peers by
  skill tag and makes either a single rr call or consumes a server-stream.
- A **two-daemon dev environment** (`scripts/two-node.sh`) so you can play
  publisher and consumer on the same laptop.
- Sane defaults in `.env.example` (just `cp .env.example .env`).

## 0. Prerequisites / 前置条件

- macOS or Linux (Windows: WSL 2).
- Python ≥ 3.9.
- `anet` binary on `$PATH`:

  ```bash
  curl -fsSL https://agentnetwork.org.cn/install.sh | sh
  anet --version
  ```

## 1. Install / 安装

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e .
# SDK from this repo:
#   pip install -e ../../sdk/python
# Or from PyPI:
#   pip install anet-sdk
```

## 2. Boot two local daemons / 起两个本地 daemon

```bash
bash scripts/two-node.sh start
# leaves daemons running in background
```

You now have:

```
daemon-1   API=http://127.0.0.1:13921   HOME=/tmp/anet-p2p-u1
daemon-2   API=http://127.0.0.1:13922   HOME=/tmp/anet-p2p-u2
```

## 3. Run your agent on daemon-1 / 在 daemon-1 上运行 agent

```bash
bash scripts/run.sh u1
```

Output should end with:

```
[service] ✓ registered name=my-agent-<hash> ans.published=True uri=agent://svc/my-agent-...
```

## 4. Discover + call from daemon-2 / 从 daemon-2 发现并调用

```bash
export ANET_BASE_URL=http://127.0.0.1:13922
export ANET_TOKEN=$(tr -d '[:space:]' < /tmp/anet-p2p-u2/.anet/api_token)
python -m my_agent.client --skill p2p
```

Expected:

```
[client] found 1 peer(s) for skill=p2p
  - 12D3KooW…  services=[my-agent-…]
[client] calling my-agent-…  HTTP 200  body={…}
[client] last audit row: my-agent-…  POST /echo  status=200  cost=0  duration=…ms
```

Streaming demo:

```bash
python -m my_agent.client --skill p2p --path /stream --stream
```

## 5. What to change / 如何改成自己的 agent

| Goal | Edit |
|---|---|
| Replace `/echo` with your business logic | `my_agent/backend.py` (vanilla FastAPI) |
| Charge per call | `.env` → `MY_SVC_FREE=false` + `MY_SVC_PER_CALL=10` |
| Add more skill tags | `.env` → `MY_SVC_TAGS=cv,llm,zh-en` |
| Non-localhost backend | daemon `~/.anet/config.json` + `MY_SVC_REMOTE_HOSTS` |
| Different daemon port | `.env` → `ANET_BASE_URL=http://...` |
| Stop the demo | Ctrl-C (service.py unregisters), then `bash scripts/two-node.sh stop` |

## 6. Where to read next / 深入阅读

- `../tutorials/00-setup.md` — full environment walkthrough
- `../tutorials/01-first-service.md` — register/discover/call explained
- `../tutorials/02-llm-service.md` — LLM with cost_model.per_call
- `../tutorials/03-multi-agent.md` — three agents talking to each other
- `../FAQ.md` — common errors and fixes
- `../examples/` — three reference apps
