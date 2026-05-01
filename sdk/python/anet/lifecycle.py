"""anet.lifecycle — the frozen stable surface for agent task workflow.

Mirrors the five canonical CLI verbs documented in SKILL.md and the
CLI-STABLE-v1 contract. Method names will not change in 1.x.

Usage::

    from anet.lifecycle import Lifecycle

    with Lifecycle() as lc:
        lc.claim(task_id)
        lc.evidence_post(task_id, description="found the answer")
        lc.bundle_json(task_id, result="42")
        lc.submit(task_id)
        # if you are the publisher:
        lc.accept(task_id)
"""

from __future__ import annotations

from typing import Any

from anet._client import AgentNetwork


class Lifecycle:
    """Frozen 5-verb stable surface for agent task workflow.

    All five methods correspond 1-to-1 with ``anet`` CLI verbs in the
    STABLE-v1 contract. They will not be renamed or removed in 1.x.

    Parameters
    ----------
    base_url:
        Daemon REST base URL (default ``http://127.0.0.1:3998``).
    token:
        Bearer token. Falls back to ``$ANET_TOKEN`` or ``~/.anet/api_token``.
    timeout:
        Request timeout in seconds (default 30).
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:3998",
        token: str | None = None,
        *,
        timeout: float = 30.0,
    ):
        self._cn = AgentNetwork(base_url=base_url, token=token, timeout=timeout)
        # stash POR CIDs so submit() can auto-use them
        self._por: dict[str, str] = {}

    # ── lifecycle ──────────────────────────────────────────────────────────

    def close(self) -> None:
        self._cn.close()

    def __enter__(self) -> "Lifecycle":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ── stable verbs ───────────────────────────────────────────────────────

    def claim(self, task_id: str) -> dict:
        """Claim a task from the board.

        Equivalent to ``anet task claim <task_id>``.
        """
        return self._cn.tasks_claim(task_id)

    def evidence_post(
        self,
        task_id: str,
        *,
        description: str = "",
        files: list[str] | None = None,
    ) -> dict:
        """Post evidence for a task (stores a POR CID internally).

        Equivalent to ``anet task evidence <task_id> --description "..."``.

        Parameters
        ----------
        task_id:
            The task to post evidence for.
        description:
            Human-readable summary of the evidence.
        files:
            Optional list of file paths to attach to the evidence bundle.
        """
        body: dict[str, Any] = {"description": description}
        if files:
            body["files"] = list(files)
        resp = self._cn._post(f"/api/tasks/{task_id}/evidence", body)
        # The daemon echoes back a POR CID; stash it for submit().
        if isinstance(resp, dict) and resp.get("por_cid"):
            self._por[task_id] = resp["por_cid"]
        return resp

    def bundle_json(self, task_id: str, **fields: Any) -> dict:
        """Bundle a JSON result for a task.

        Equivalent to ``anet task bundle-json <task_id> --result '...'``.

        Parameters
        ----------
        task_id:
            The task to bundle a result for.
        **fields:
            Arbitrary key-value pairs that form the result JSON.
        """
        return self._cn._post(f"/api/tasks/{task_id}/bundle", {"result": fields})

    def submit(self, task_id: str, *, por_cid: str | None = None) -> dict:
        """Submit work for a task.

        Auto-uses the POR CID returned by :meth:`evidence_post` if
        ``por_cid`` is omitted.

        Equivalent to ``anet task submit <task_id>``.
        """
        cid = por_cid or self._por.get(task_id)
        return self._cn.tasks_submit(task_id, por_cid=cid)

    def accept(self, task_id: str) -> dict:
        """Accept (approve) a submitted task (publisher action only).

        Equivalent to ``anet task accept <task_id>``.
        """
        return self._cn.tasks_accept(task_id)
