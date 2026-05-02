"""API 转转 bank 后端：A 存 key，B 借 key。

所有调用基于 AgentNetwork，这里只暴露 HTTP 供 daemon 反代。
规则：
  - 存 key 直接挂牌（不做上游验证）
  - 只有存过的 DID 才能借
  - 借一次就没（一次性），但完整备份
"""
import logging
import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from bank import Bank

PORT = int(os.environ.get("PORT", "7200"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] bank: %(message)s",
)
logger = logging.getLogger(__name__)

bank = Bank()

app = FastAPI(title="API 转转 Bank", version="3.0.0")


# ---------- 元信息 ----------
@app.get("/health")
async def health():
    a = bank.audit()
    return {
        "ok": True,
        "members": a["members"],
        "deposits_available": a["deposits_available"],
        "deposits_leased": a["deposits_leased"],
    }


@app.get("/meta")
async def meta():
    return {
        "name": "api-zhuanzhuan-bank",
        "version": "3.0.0",
        "endpoints": [
            {"method": "POST", "path": "/deposit",  "desc": "A 存 key（需 X-Agent-DID）"},
            {"method": "POST", "path": "/lease",    "desc": "B 借 key（需 X-Agent-DID，必须是会员）"},
            {"method": "GET",  "path": "/audit",    "desc": "查看全部记录"},
            {"method": "GET",  "path": "/deposits", "desc": "查看所有挂牌（脱敏）"},
            {"method": "GET",  "path": "/health"},
        ],
        "rule": "deposit first to become a member, then you can lease (one-time) from other members' keys",
    }


# ---------- deposit ----------
class DepositReq(BaseModel):
    api_key: str
    base_url: str = Field(..., description="上游 API 根 URL，如 https://api.openai-next.com")
    model: str = Field(..., description="模型名，如 claude-opus-4-7")


@app.post("/deposit")
async def deposit(
    req: DepositReq,
    x_agent_did: str = Header(None, alias="X-Agent-DID"),
):
    if not x_agent_did:
        raise HTTPException(400, "missing X-Agent-DID header")
    result = bank.deposit(x_agent_did, req.api_key, req.base_url, req.model)
    if not result["ok"]:
        logger.info("deposit rejected: did=%s reason=%s", x_agent_did, result["detail"])
        raise HTTPException(400, f"deposit rejected: {result['detail']}")
    logger.info("deposit ok: did=%s dep_id=%s", x_agent_did, result["deposit_id"])
    return result


# ---------- lease ----------
@app.post("/lease")
async def lease(x_agent_did: str = Header(None, alias="X-Agent-DID")):
    if not x_agent_did:
        raise HTTPException(400, "missing X-Agent-DID header")
    result = bank.lease(x_agent_did)
    if not result["ok"]:
        code = 403 if "not a member" in result["detail"] else 404
        logger.info("lease rejected: did=%s reason=%s", x_agent_did, result["detail"])
        raise HTTPException(code, result["detail"])
    logger.info(
        "lease ok: did=%s lease_id=%s from=%s",
        x_agent_did, result["key_payload"]["lease_id"], result["key_payload"]["provider_did"],
    )
    return result


# ---------- 审计 ----------
@app.get("/audit")
async def audit():
    return bank.audit()


@app.get("/deposits")
async def deposits():
    return {"deposits": bank.list_deposits_safe()}


if __name__ == "__main__":
    import uvicorn
    logger.info("bank starting on 127.0.0.1:%d", PORT)
    uvicorn.run(app, host="127.0.0.1", port=PORT)
