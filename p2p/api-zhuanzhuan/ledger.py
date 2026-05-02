"""虚拟账本（不接真支付）。

- 每个 caller_did 首次出现自动开户，初始余额 INITIAL_CREDIT 美金
- 扣费源：上游 LLM 响应 usage.cost（美金）
- 数据存 JSON 文件，重启不丢
- 不并发安全到生产级（玩具级 lock）
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Optional

INITIAL_CREDIT = float(os.environ.get("INITIAL_CREDIT", "20.0"))
LEDGER_PATH = Path(os.environ.get("LEDGER_PATH", "/Users/edy/Desktop/API转转/data/ledger.json"))


class Ledger:
    def __init__(self, path: Path = LEDGER_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"accounts": {}, "txns": []}
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {"accounts": {}, "txns": []}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))
        tmp.replace(self.path)

    # ---------- 账户 ----------
    def _ensure_account(self, did: str) -> dict:
        acc = self._data["accounts"].get(did)
        if acc is None:
            acc = {"balance": INITIAL_CREDIT, "spent": 0.0, "calls": 0, "opened_at": time.time()}
            self._data["accounts"][did] = acc
        return acc

    def balance(self, did: str) -> dict:
        with self._lock:
            acc = self._ensure_account(did)
            self._save()
            return dict(acc)

    def has_funds(self, did: str, min_amount: float = 0.0) -> bool:
        with self._lock:
            acc = self._ensure_account(did)
            return acc["balance"] > min_amount

    def charge(self, did: str, amount: float, note: str = "") -> dict:
        """按 amount 美金扣费。返回扣完后的账户状态。"""
        with self._lock:
            acc = self._ensure_account(did)
            acc["balance"] = round(acc["balance"] - amount, 6)
            acc["spent"] = round(acc["spent"] + amount, 6)
            acc["calls"] += 1
            self._data["txns"].append({
                "ts": time.time(), "did": did, "amount": amount, "note": note,
                "balance_after": acc["balance"],
            })
            # 限制流水大小
            if len(self._data["txns"]) > 5000:
                self._data["txns"] = self._data["txns"][-3000:]
            self._save()
            return dict(acc)

    def list_accounts(self) -> dict:
        with self._lock:
            return dict(self._data["accounts"])

    def recent_txns(self, did: Optional[str] = None, limit: int = 50) -> list:
        with self._lock:
            txns = self._data["txns"]
            if did:
                txns = [t for t in txns if t["did"] == did]
            return txns[-limit:]
