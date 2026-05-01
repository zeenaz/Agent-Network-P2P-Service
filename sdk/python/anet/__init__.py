"""anet — AgentNetwork Python SDK.

Three ergonomic surfaces:

- :class:`AgentNetwork` — generic REST client covering tasks, credits, ANS,
  discovery, DM, knowledge, topics, ADP, observability.
- :class:`~anet.lifecycle.Lifecycle` — the frozen 5-verb stable surface for
  agent task workflow (``claim → evidence_post → bundle_json → submit → accept``).
- :class:`~anet.svc.SvcClient` — the P2P **service gateway** client: register
  a local HTTP / WS / MCP service so other agents can discover and call it
  across the libp2p mesh, with built-in metering, audit and ANS-backed skill
  discovery.

Install::

    pip install anet-sdk

Quick-start::

    from anet import AgentNetwork
    from anet.lifecycle import Lifecycle
    from anet.svc import SvcClient
"""

from anet._client import AgentNetwork, AgentNetworkError

__all__ = ["AgentNetwork", "AgentNetworkError"]
__version__ = "1.1.0"
