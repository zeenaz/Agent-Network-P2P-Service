"""Agent A — 供应商 (Supplier). 持有产品数据 context + product_info skill."""

import os
import threading
from typing import Optional
import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from register import register_agent

NAME = "supplier-shenzhen"
PORT = int(os.environ.get("AGENT_A_PORT", "7411"))
PER_CALL = int(os.environ.get("AGENT_A_PER_CALL", "0"))

app = FastAPI(title=NAME)

# ========== Context: 真实产品数据库 ==========
PRODUCTS = {
    "电动滑板车": {
        "hs_code": "8711.6000",
        "price_usd": 289.00,
        "moq": 100,
        "weight_kg": 22.0,
        "material": "铝合金车架 + 锂电池",
        "battery_type": "锂离子 36V/10.4Ah",
        "cert_have": ["CE", "RoHS"],
        "cert_missing": ["UN38.3", "REACH"],
        "origin": "深圳",
    },
    "蓝牙耳机": {
        "hs_code": "8518.3000",
        "price_usd": 36.00,
        "moq": 500,
        "weight_kg": 0.2,
        "material": "ABS塑料 + 电子元件",
        "battery_type": "锂聚合物 3.7V/50mAh",
        "cert_have": ["CE", "RoHS"],
        "cert_missing": [],
        "origin": "东莞",
    },
    "锂电池": {
        "hs_code": "8507.6000",
        "price_usd": 45.00,
        "moq": 200,
        "weight_kg": 1.5,
        "material": "锂离子电芯 + 钢壳",
        "battery_type": "锂离子 12.8V/20Ah",
        "cert_have": ["UN38.3", "CE"],
        "cert_missing": ["MSDS"],
        "origin": "宁德",
    },
    "户外储能电源": {
        "hs_code": "8507.6000",
        "price_usd": 599.00,
        "moq": 50,
        "weight_kg": 8.5,
        "material": "锂离子电池组 + 铝合金外壳",
        "battery_type": "锂离子 48V/50Ah",
        "cert_have": ["CE", "RoHS", "UN38.3"],
        "cert_missing": ["REACH", "CBAM"],
        "origin": "深圳",
    },
    "儿童玩具车": {
        "hs_code": "9503.0000",
        "price_usd": 39.00,
        "moq": 1000,
        "weight_kg": 2.0,
        "material": "ABS塑料 + 电子元件 + 锂电池",
        "battery_type": "锂聚合物 7.4V/2Ah",
        "cert_have": ["CE", "EN71"],
        "cert_missing": ["TSR新规", "REACH"],
        "origin": "汕头",
    },
}


@app.get("/health")
def health(): return {"ok": True, "agent": NAME}

@app.get("/meta")
def meta():
    return {
        "name": NAME, "version": "0.1.0", "skill": "product_info",
        "description": "供应商：持有产品数据库，提供产品规格与报价",
        "products_available": list(PRODUCTS.keys()),
    }

@app.post("/v1/product/list")
async def list_products():
    """返回所有产品列表"""
    return JSONResponse({"products": [
        {"name": n, "price_usd": p["price_usd"], "moq": p["moq"],
         "origin": p["origin"], "hs_code": p["hs_code"]}
        for n, p in PRODUCTS.items()
    ]})

@app.post("/v1/product/detail")
async def product_detail(req: Request):
    """返回指定产品的完整规格"""
    body = await req.json()
    name = (body or {}).get("product", "")
    p = PRODUCTS.get(name)
    if not p:
        # 模糊匹配
        matches = [n for n in PRODUCTS if name in n]
        if matches:
            p = PRODUCTS[matches[0]]
            name = matches[0]
        else:
            return JSONResponse({"error": f"未知产品: {name}", "available": list(PRODUCTS.keys())})
    return JSONResponse({
        "product": name,
        "hs_code": p["hs_code"],
        "price_usd": p["price_usd"],
        "moq": p["moq"],
        "weight_kg": p["weight_kg"],
        "material": p["material"],
        "battery_type": p["battery_type"],
        "cert_have": p["cert_have"],
        "cert_missing": p["cert_missing"],
        "origin": p["origin"],
    })

@app.post("/v1/quote")
async def quote(req: Request):
    """估算产品成本"""
    body = await req.json()
    name = (body or {}).get("product", "")
    try:
        qty = int((body or {}).get("qty", 100))
    except ValueError:
        return JSONResponse({"error": "数量格式错误", "status": 400})
    p = PRODUCTS.get(name)
    if not p:
        matches = [n for n in PRODUCTS if name in n]
        if matches:
            p = PRODUCTS[matches[0]]
            name = matches[0]
        else:
            return JSONResponse({"error": f"未知产品: {name}"})
    if qty < p["moq"]:
        return JSONResponse({"error": f"最小起订量 {p['moq']} 件", "moq": p["moq"]})
    subtotal = round(p["price_usd"] * qty, 2)
    return JSONResponse({
        "product": name,
        "qty": qty,
        "unit_price_usd": p["price_usd"],
        "subtotal_usd": subtotal,
        "origin": p["origin"],
        "weight_total_kg": round(p["weight_kg"] * qty, 1),
        "cert_provided": p["cert_have"],
        "cert_maybe_needed": p["cert_missing"],
    })


@app.post("/v1/chat")
async def supplier_chat(req: Request):
    """聊天接口 — 供应商回答产品相关问题"""
    body = await req.json()
    msg = (body or {}).get("message", "") or (body or {}).get("text", "") or (body or {}).get("prompt", "")
    know = {
        "产品": f"我们有 {len(PRODUCTS)} 款产品，包括: {', '.join(PRODUCTS.keys())}。提供详细规格和报价。",
        "价格": f"产品价格从 ${min(p['price_usd'] for p in PRODUCTS.values())} 到 ${max(p['price_usd'] for p in PRODUCTS.values())} 不等",
        "交货": "一般交货期 15-30 天，具体看产品和数量。",
        "证书": "我们有 CE、RoHS、UN38.3、EN71 等认证，具体看产品。",
        "默认": f"我是深圳工厂的供应商 Agent，我可以查询产品规格、报价和认证信息。试试问我「产品有哪些」「价格」「电动滑板车」",
    }
    for kw, reply in know.items():
        if kw in msg:
            return JSONResponse({"reply": reply, "agent": NAME})
    # 试试查产品
    for pname in PRODUCTS:
        if pname in msg:
            p = PRODUCTS[pname]
            return JSONResponse({"reply": f"{pname}: ${p['price_usd']}/台, MOQ={p['moq']}, HS编码={p['hs_code']}, 产地{p['origin']}", "agent": NAME})
    return JSONResponse({"reply": know["默认"], "agent": NAME})


def main():
    threading.Thread(
        target=lambda: register_agent(
            NAME, PORT,
            paths=["/v1/product/list", "/v1/product/detail", "/v1/quote", "/v1/chat", "/health", "/meta"],
            tags=["product_info", "supplier", "trade"],
            description="供应商 Agent：产品数据库 + 报价 (真实出口数据)",
            per_call=PER_CALL,
        ), daemon=True,
    ).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

if __name__ == "__main__":
    main()
