# Application Themes / 赛题方向

Six directions for what to build on the AgentNetwork P2P gateway. Use these as
creative starting points — combine them, remix them, or go somewhere completely
different.

---

## 01 🤖 AI Skill Marketplace / AI 技能集市

Build a multi-node marketplace where agents expose specialised AI capabilities
(OCR, translation, summarisation, code review) as priced P2P services. A
"broker" agent discovers services by skill tag, routes requests to the cheapest
or fastest provider, and earns a commission.

**Key APIs:** `svc.register(per_call=N, tags=["ocr"])`, `svc.discover(skill="ocr")`,
`svc.audit()` for settlement.

---

## 02 🔗 Decentralised Data Pipeline / 去中心化数据流水线

Connect multiple agents into a processing pipeline: ingestion → transform →
enrich → store, where each stage is a separate P2P service. Use the
`server-stream` mode to pass large payloads as a stream rather than loading
everything into memory.

**Key APIs:** `svc.stream(mode="server-stream")`, chained `svc.call()`.

---

## 03 🎯 Federated RAG / 联邦检索增强生成

Each agent holds a private knowledge shard. A query-routing agent fans out to
multiple RAG workers, re-ranks the results, and synthesises a final answer —
all without centralising the data.

**Key APIs:** `svc.discover(skill="rag")`, parallel fan-out with
`concurrent.futures`, result re-ranking in the orchestrator.

---

## 04 💰 Pay-Per-Use API Gateway / 按用量付费的 API 网关

Wrap any third-party HTTP API (weather, maps, financial data) as a billable P2P
service. Use `per_kb` billing to charge proportionally to the data returned.
Add a caching layer to serve cached results for free while charging for fresh
fetches.

**Key APIs:** `svc.register(per_kb=1)`, `X-Agent-DID` header for
per-caller rate limiting.

---

## 05 🛡️ Collaborative Threat Intelligence / 协同威胁情报

Agents share threat indicators (IP blocklists, malware hashes) as free
broadcast services. A coordinator subscribes to multiple sources, deduplicates,
and exposes a unified feed as a priced service to downstream consumers.

**Key APIs:** `svc.discover(skill="threat-intel")`, audit log for provenance,
free registration with `free=True`.

---

## 06 🎨 Creative Collective / 创意协作网络

Multiple specialised creative agents (image generation, music synthesis, story
writing) collaborate on a single user request. An orchestrator breaks the
request into subtasks, assigns each to the best-fit agent by skill, and stitches
the outputs back together.

**Key APIs:** Multi-skill discovery, `svc.stream()` for incremental creative
output, audit log for attribution.
