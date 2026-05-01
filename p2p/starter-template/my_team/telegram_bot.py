"""Telegram Bot — 通过 Telegram 操控 P2P Agent 网络。

用法:
  1. 找 @BotFather 创一个 bot，拿到 token
  2. BOT_TOKEN=xxx python3 my_team/telegram_bot.py

命令:
  /start     — 查看帮助
  /agents    — 列出所有可对话的 Agent
  /chat      — 跟指定 Agent 聊天: /chat <agent名> <消息>
  /discover  — 搜索 Agent: /discover <skill>
  /inbox     — 查看收到的消息
  /broadcast — 广播消息到全网
"""

import os
import sys
import time
import json
import threading

import httpx
from anet.svc import SvcClient

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANET_BASE = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13922")
ANET_TOKEN = os.environ.get("ANET_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

if not BOT_TOKEN:
    print("✗ 需要设置 BOT_TOKEN 环境变量")
    print("  找 @BotFather 创建 bot: https://t.me/BotFather")
    sys.exit(1)


def tg(method, data=None):
    """调 Telegram Bot API"""
    url = f"{API_URL}/{method}"
    try:
        r = httpx.post(url, json=data or {}, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[tg] API error: {e}")
        return {"ok": False}


def discover_agents() -> list[dict]:
    """扫描全网可对话 Agent"""
    seen = set()
    agents = []
    skills = ["chat", "analysis", "translate", "llm", "search", "agent", "api",
              "bot", "trade", "data", "knowledge", "review", "code", "sentiment"]
    try:
        svc = SvcClient(base_url=ANET_BASE)
        for skill in skills:
            try:
                for p in svc.discover(skill=skill):
                    for s in p.get("services", []):
                        if s["name"] not in seen:
                            seen.add(s["name"])
                            agents.append({
                                "name": s["name"],
                                "peer_id": p["peer_id"],
                                "skill": skill,
                                "desc": s.get("description", ""),
                            })
            except Exception:
                pass
        svc.close()
    except Exception:
        pass
    return agents


def chat_agent(peer_id: str, service: str, message: str) -> str:
    """给指定 Agent 发消息"""
    paths = ["/v1/chat", "/api/chat", "/chat", "/v1/generate",
             "/v1/completion", "/v1/analyze", "/api/query"]
    for path in paths:
        try:
            svc = SvcClient(base_url=ANET_BASE)
            resp = svc.call(peer_id, service, path, method="POST",
                body={"message": message, "text": message, "prompt": message})
            svc.close()
            body = resp.get("body") or {}
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except Exception:
                    pass
            if isinstance(body, dict):
                if body.get("error"):
                    continue
                reply = (body.get("reply") or body.get("completion") or
                         body.get("result") or body.get("text") or
                         body.get("translated") or body.get("summary") or
                         body.get("message"))
                if reply:
                    return reply
                # 找第一个字符串值
                for v in body.values():
                    if isinstance(v, str) and len(v) > 5:
                        return v
                return json.dumps(body, ensure_ascii=False)
            return str(body)
        except Exception:
            continue
    return "⚠️ 该 Agent 没有聊天接口"


def send_msg(chat_id, text, parse_mode=None):
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    tg("sendMessage", data)


def handle_message(chat_id, text):
    text = text.strip()

    if text == "/start":
        send_msg(chat_id,
            "🤖 *P2P Agent 网络 — Telegram Bot*\n\n"
            "你可以通过我操控整个 P2P Agent 网络：\n\n"
            "`/agents` — 列出所有可对话的 Agent\n"
            "`/chat <名字> <消息>` — 跟 Agent 聊天\n"
            "`/discover <skill>` — 按技能搜索 Agent\n"
            "`/inbox` — 查看收到的消息\n"
            "`/broadcast <内容>` — 广播到全网\n\n"
            "例如: `/chat supplier-shenzhen 你们有什么产品`",
            parse_mode="Markdown")

    elif text == "/agents":
        send_msg(chat_id, "🔍 正在扫描网络上的 Agent...")
        agents = discover_agents()
        if not agents:
            send_msg(chat_id, "⚠️ 没找到可对话的 Agent")
            return
        lines = [f"📡 共 {len(agents)} 个可对话 Agent:\n"]
        for a in agents:
            lines.append(f"• *{a['name']}*  `{a['skill']}`")
            if a['desc']:
                lines.append(f"  _{a['desc'][:50]}_")
        # Telegram 限制 4096 字符，分批发送
        msg = "\n".join(lines)
        if len(msg) > 4000:
            msg = "\n".join(lines[:30]) + f"\n\n...还有 {len(agents)-30} 个"
        send_msg(chat_id, msg, parse_mode="Markdown")

    elif text.startswith("/chat "):
        parts = text[6:].strip().split(" ", 1)
        if len(parts) < 2:
            send_msg(chat_id, "用法: `/chat <Agent名> <消息>`\n例如: `/chat supplier-shenzhen 有什么产品`",
                     parse_mode="Markdown")
            return
        name, message = parts
        send_msg(chat_id, f"💬 正在问 *{name}*...", parse_mode="Markdown")
        # 先查到这个 Agent
        agents = discover_agents()
        target = next((a for a in agents if a["name"] == name), None)
        if not target:
            send_msg(chat_id, f"⚠️ 找不到叫 {name} 的 Agent，试试 /agents 查看列表")
            return
        reply = chat_agent(target["peer_id"], target["name"], message)
        send_msg(chat_id, f"*{name}* 回复:\n{reply}", parse_mode="Markdown")

    elif text.startswith("/discover "):
        skill = text[10:].strip()
        send_msg(chat_id, f"🔍 搜索 skill={skill}...")
        try:
            svc = SvcClient(base_url=ANET_BASE)
            peers = svc.discover(skill=skill)
            svc.close()
            if not peers:
                send_msg(chat_id, f"⚠️ 没找到 skill={skill} 的 Agent")
                return
            lines = [f"✅ 找到 {len(peers)} 个 skill={skill}:\n"]
            for p in peers:
                for s in p.get("services", []):
                    lines.append(f"• *{s['name']}*  _{s.get('description','')[:40]}_")
            send_msg(chat_id, "\n".join(lines), parse_mode="Markdown")
        except Exception as e:
            send_msg(chat_id, f"⚠️ 搜索失败: {e}")

    elif text == "/inbox":
        try:
            r = httpx.get(f"{ANET_BASE}/api/dm/inbox",
                          headers={"Authorization": f"Bearer {ANET_TOKEN}"}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                msgs = data if isinstance(data, list) else data.get("messages", data.get("inbox", []))
                if not msgs:
                    send_msg(chat_id, "📭 收件箱为空")
                    return
                lines = [f"📥 共 {len(msgs)} 条消息:\n"]
                for m in msgs[-5:]:
                    sender = m.get("sender", m.get("from", "?"))
                    body = m.get("body", m.get("text", ""))
                    lines.append(f"• *{sender}*: {body[:100]}")
                send_msg(chat_id, "\n".join(lines), parse_mode="Markdown")
            else:
                send_msg(chat_id, "⚠️ 无法读取收件箱")
        except Exception as e:
            send_msg(chat_id, f"⚠️ 错误: {e}")

    elif text.startswith("/broadcast "):
        msg = text[11:].strip()
        if not msg:
            send_msg(chat_id, "用法: /broadcast <消息内容>")
            return
        try:
            r = httpx.post(f"{ANET_BASE}/api/brain/intent",
                headers={"Authorization": f"Bearer {ANET_TOKEN}", "Content-Type": "application/json"},
                json={"subject": "telegram-broadcast", "object": msg, "tags": ["broadcast"]},
                timeout=5)
            send_msg(chat_id, f"📡 已广播:\n{msg}")
        except Exception as e:
            send_msg(chat_id, f"⚠️ 广播失败: {e}")

    else:
        send_msg(chat_id,
            "未知命令，试试:\n"
            "`/agents` 查看所有 Agent\n"
            "`/chat <名字> <消息>` 聊天\n"
            "`/start` 查看帮助",
            parse_mode="Markdown")


def main():
    print(f"[bot] 启动 Telegram Bot...")
    print(f"[bot] API: {ANET_BASE}")
    print(f"[bot] 等待消息...")

    offset = 0
    while True:
        try:
            updates = tg("getUpdates", {"offset": offset, "timeout": 30})
            if updates.get("ok") and updates.get("result"):
                for u in updates["result"]:
                    offset = u["update_id"] + 1
                    if "message" in u and "text" in u["message"]:
                        chat_id = u["message"]["chat"]["id"]
                        text = u["message"]["text"]
                        print(f"[bot] ← {chat_id}: {text}")
                        threading.Thread(target=handle_message,
                            args=(chat_id, text), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[boot] 停止")
            break
        except Exception as e:
            print(f"[bot] polling error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
