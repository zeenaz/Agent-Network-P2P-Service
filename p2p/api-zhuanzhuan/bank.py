"""API 转转 bank：存 key / 借 key，一次性，全备份。

规则：
  - A deposit → 直接入库 → 生成 deposit_id
  - 存过 key 的 DID 成为 "会员"
  - 只有会员能 lease（借）
  - 借到一把后该 key 从可用池删除（阅后即焚），但备份表永留
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

BANK_PATH = Path(os.environ.get("BANK_PATH", "/Users/edy/Desktop/API转转/data/bank.json"))


class Bank:
    def __init__(self, path: Path = BANK_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {
                "deposits": {},   # id -> {provider_did, api_key, base_url, model, status, deposited_at}
                "leases": [],     # [{lease_id, deposit_id, borrower_did, leased_at, snapshot}]
                "members": {},    # did -> {first_deposit_at, total_deposits}
            }
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {"deposits": {}, "leases": [], "members": {}}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))
        tmp.replace(self.path)

    # ---------- deposit ----------
    def deposit(
        self,
        provider_did: str,
        api_key: str,
        base_url: str,
        model: str,
    ) -> dict:
        """A 存 key。直接入库，不做上游验证。返回 {ok, deposit_id, detail}。"""
        dep_id = f"dep_{uuid.uuid4().hex[:12]}"
        now = time.time()
        with self._lock:
            self._data["deposits"][dep_id] = {
                "deposit_id": dep_id,
                "provider_did": provider_did,
                "api_key": api_key,
                "base_url": base_url.rstrip("/"),
                "model": model,
                "status": "available",   # available | leased
                "deposited_at": now,
            }
            m = self._data["members"].get(provider_did)
            if m is None:
                self._data["members"][provider_did] = {
                    "first_deposit_at": now,
                    "total_deposits": 1,
                }
            else:
                m["total_deposits"] += 1
            self._save()
        return {"ok": True, "deposit_id": dep_id, "detail": "stored"}

    # ---------- lease ----------
    def is_member(self, did: str) -> bool:
        with self._lock:
            return did in self._data["members"]

    def lease(self, borrower_did: str) -> dict:
        """B 借一把。只有会员能借。一次性。返回 {ok, key_payload, detail}。"""
        with self._lock:
            if borrower_did not in self._data["members"]:
                return {
                    "ok": False,
                    "key_payload": None,
                    "detail": "not a member: you must deposit first",
                }
            # 找一把不是借用者自己存的 available
            for dep_id, dep in self._data["deposits"].items():
                if dep["status"] != "available":
                    continue
                if dep["provider_did"] == borrower_did:
                    continue  # 不能借自己的
                # 命中
                dep["status"] = "leased"
                lease_id = f"lease_{uuid.uuid4().hex[:12]}"
                snapshot = {
                    "api_key": dep["api_key"],
                    "base_url": dep["base_url"],
                    "model": dep["model"],
                }
                self._data["leases"].append({
                    "lease_id": lease_id,
                    "deposit_id": dep_id,
                    "borrower_did": borrower_did,
                    "provider_did": dep["provider_did"],
                    "leased_at": time.time(),
                    "snapshot": snapshot,
                })
                self._save()
                return {
                    "ok": True,
                    "key_payload": {
                        "lease_id": lease_id,
                        "api_key": dep["api_key"],
                        "base_url": dep["base_url"],
                        "model": dep["model"],
                        "provider_did": dep["provider_did"],
                    },
                    "detail": "leased (one-time, key retired from pool)",
                }
            return {
                "ok": False,
                "key_payload": None,
                "detail": "pool empty: no available keys (from other members)",
            }

    # ---------- audit ----------
    def audit(self) -> dict:
        with self._lock:
            available = sum(1 for d in self._data["deposits"].values() if d["status"] == "available")
            leased = sum(1 for d in self._data["deposits"].values() if d["status"] == "leased")
            return {
                "members": len(self._data["members"]),
                "deposits_total": len(self._data["deposits"]),
                "deposits_available": available,
                "deposits_leased": leased,
                "leases_total": len(self._data["leases"]),
                "recent_leases": self._data["leases"][-10:],
                "members_detail": self._data["members"],
            }

    def list_deposits_safe(self) -> list:
        """不暴露真 key，脱敏。"""
        with self._lock:
            return [
                {
                    "deposit_id": d["deposit_id"],
                    "provider_did": d["provider_did"],
                    "base_url": d["base_url"],
                    "model": d["model"],
                    "status": d["status"],
                    "deposited_at": d["deposited_at"],
                    "key_preview": d["api_key"][:6] + "..." + d["api_key"][-4:],
                }
                for d in self._data["deposits"].values()
            ]
