"""key 池：A 存 key，按模型分类，调用时按模型挑一个。

- 不真实扣 A 的 key（虚拟记账由 ledger.py 负责）
- 简单轮询挑 key
- 数据存 JSON 文件
"""
from __future__ import annotations

import itertools
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

POOL_PATH = Path(os.environ.get("KEY_POOL_PATH", "/Users/edy/Desktop/API转转/data/key_pool.json"))


class KeyPool:
    def __init__(self, path: Path = POOL_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data = self._load()
        self._cycles: dict[str, itertools.cycle] = {}

    def _load(self) -> dict:
        if not self.path.exists():
            return {"keys": {}}  # key_id -> entry
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {"keys": {}}

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))
        tmp.replace(self.path)

    # ---------- 存款 ----------
    def deposit(
        self,
        provider: str,
        api_key: str,
        models: list[str],
        base_url: str = "https://api.openai-next.com",
    ) -> str:
        kid = uuid.uuid4().hex[:12]
        with self._lock:
            self._data["keys"][kid] = {
                "key_id": kid,
                "provider": provider,
                "api_key": api_key,
                "models": [m.lower() for m in models],
                "base_url": base_url.rstrip("/"),
                "added_at": time.time(),
                "active": True,
                "calls": 0,
            }
            self._save()
            self._cycles.clear()
        return kid

    def remove(self, key_id: str) -> bool:
        with self._lock:
            if key_id not in self._data["keys"]:
                return False
            del self._data["keys"][key_id]
            self._save()
            self._cycles.clear()
        return True

    # ---------- 撮合 ----------
    def pick(self, model: str) -> Optional[dict]:
        """按模型挑一个活跃 key（轮询）。"""
        m = model.lower()
        with self._lock:
            candidates = [
                e for e in self._data["keys"].values()
                if e["active"] and (not e["models"] or m in e["models"] or "*" in e["models"])
            ]
            if not candidates:
                return None
            cycle = self._cycles.get(m)
            if cycle is None:
                cycle = itertools.cycle(range(len(candidates)))
                self._cycles[m] = cycle
            idx = next(cycle) % len(candidates)
            chosen = candidates[idx]
            chosen["calls"] += 1
            self._save()
            return dict(chosen)

    # ---------- 列表（脱敏） ----------
    def list_safe(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "key_id": e["key_id"],
                    "provider": e["provider"],
                    "models": e["models"],
                    "base_url": e["base_url"],
                    "added_at": e["added_at"],
                    "active": e["active"],
                    "calls": e["calls"],
                    "key_preview": e["api_key"][:6] + "..." + e["api_key"][-4:],
                }
                for e in self._data["keys"].values()
            ]
