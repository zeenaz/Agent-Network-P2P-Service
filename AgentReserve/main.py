"""API转转: AgentNetwork 永远在线的中转 Agent。

别人调用本服务 HTTP /proxy --> 本服务通过 anet-sdk 调目标 peer --> 返回结果。

前置：
  1. pip install anet-sdk
  2. anet daemon &        # 必须先启动本地 daemon
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import API_KEY, ALLOWED_PEERS
from router import AgentNetClient
from registrar import Registrar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

client = AgentNetClient()
registrar = Registrar(client)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        info = registrar.register()
        logger.info("api-zhuanzhuan online: %s", info.get("ans") or info.get("name"))
    except Exception as e:
        logger.error("startup register failed: %s (服务照常启动，可稍后手动注册)", e)
    yield
    try:
        registrar.unregister()
    finally:
        client.close()
        logger.info("api-zhuanzhuan offline")


app = FastAPI(title="API转转 Relay Agent", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ---------- auth ----------
def auth(authorization: Optional[str] = Header(None)) -> str:
    if not API_KEY:
        return "anonymous"
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization[7:]
    if token != API_KEY:
        raise HTTPException(403, "invalid token")
    return token


# ---------- schemas ----------
class ProxyRequest(BaseModel):
    target_peer_id: str = Field(..., description="目标 Agent 的 peer_id")
    service: str = Field(..., description="目标 Agent 上注册的服务名")
    path: str = Field("/", description="目标服务下的路径")
    method: str = Field("POST", description="HTTP 方法")
    body: dict = Field(default_factory=dict)
    caller_did: Optional[str] = Field(None, description="透传调用方身份")


class ProxyResponse(BaseModel):
    status: int
    body: object
    cost: Optional[int] = None
    error: Optional[str] = None


# ---------- endpoints ----------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "name": "api-zhuanzhuan",
        "registered": registrar.registered,
        "ans": registrar.info.get("ans") if registrar.registered else None,
    }


@app.get("/discover")
def discover(skill: str, limit: int = 10, _: str = Depends(auth)):
    peers = client.discover(skill, limit=limit)
    return {"skill": skill, "peers": peers}


@app.post("/proxy", response_model=ProxyResponse)
def proxy(req: ProxyRequest, _: str = Depends(auth)):
    if ALLOWED_PEERS and req.target_peer_id not in ALLOWED_PEERS:
        raise HTTPException(403, f"peer {req.target_peer_id} not in whitelist")
    try:
        result = client.call(
            peer_id=req.target_peer_id,
            service=req.service,
            path=req.path,
            method=req.method,
            body=req.body,
            caller_did=req.caller_did,
        )
    except Exception as e:
        logger.exception("proxy failed")
        raise HTTPException(502, f"upstream error: {e}")
    return ProxyResponse(
        status=result.get("status", 0),
        body=result.get("body"),
        cost=result.get("cost"),
        error=result.get("error"),
    )


@app.get("/")
def root():
    return {"service": "api-zhuanzhuan", "docs": "/docs"}
