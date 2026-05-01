"""Agent C — 物流 (Logistics). 持有运价数据库 context + shipping_quote skill."""

import os
import threading
from typing import Optional
import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from anet.svc import SvcClient
from register import register_agent

NAME = "logistics-shipper"
PORT = int(os.environ.get("AGENT_C_PORT", "7413"))
PER_CALL = int(os.environ.get("AGENT_C_PER_CALL", "0"))
ANET_BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")

app = FastAPI(title=NAME)

# ========== Context: 真实物流运价数据库 (2025-2026) ==========
ROUTES = {
    "深圳→汉堡": {
        "port_origin": "深圳盐田",
        "port_dest": "汉堡",
        "transit_days": 28,
        "lcl_usd_per_cbm": 95,
        "fcl_20gp_usd": 1150,
        "fcl_40hq_usd": 1400,
    },
    "深圳→鹿特丹": {
        "port_origin": "深圳盐田",
        "port_dest": "鹿特丹",
        "transit_days": 30,
        "lcl_usd_per_cbm": 90,
        "fcl_20gp_usd": 1100,
        "fcl_40hq_usd": 1350,
    },
    "深圳→热那亚": {
        "port_origin": "深圳盐田",
        "port_dest": "热那亚",
        "transit_days": 26,
        "lcl_usd_per_cbm": 115,
        "fcl_20gp_usd": 1300,
        "fcl_40hq_usd": 1580,
    },
    "上海→汉堡": {
        "port_origin": "上海洋山",
        "port_dest": "汉堡",
        "transit_days": 30,
        "lcl_usd_per_cbm": 90,
        "fcl_20gp_usd": 1100,
        "fcl_40hq_usd": 1350,
    },
    "上海→鹿特丹": {
        "port_origin": "上海洋山",
        "port_dest": "鹿特丹",
        "transit_days": 32,
        "lcl_usd_per_cbm": 85,
        "fcl_20gp_usd": 1080,
        "fcl_40hq_usd": 1300,
    },
}

SURCHARGES = {
    "BAF": {"name": "燃油附加费", "rate": "基本运费的 15%"},
    "CAF": {"name": "货币贬值附加费", "rate": "基本运费的 8%"},
    "THC": {"name": "码头操作费", "rate": "¥600-900/柜"},
    "ETS": {"name": "欧盟碳排放附加费", "rate": "2026 年起全面计入, 约 €25-50/TEU"},
    "hazmat": {"name": "危险品附加费", "rate": "$50-150/柜 (含锂电池产品)"},
}

HS_SURCHARGE_MAP = {
    "8711": ["BAF", "CAF", "THC", "hazmat", "ETS"],
    "8507": ["BAF", "CAF", "THC", "hazmat", "MSDS", "ETS"],
    "8518": ["BAF", "CAF", "THC", "ETS"],
    "9503": ["BAF", "CAF", "THC", "ETS"],
}


def _estimate_cbm(weight_kg: float, qty: int) -> float:
    """估算体积 (m³)。规则: 1CBM ≈ 167kg 为标准密度"""
    est_cbm = round(weight_kg * qty / 167, 2)
    return max(est_cbm, 0.1)  # 至少 0.1 CBM


def _pick_route(origin: str, dest: str) -> dict | None:
    """智能匹配路线"""
    # 直接匹配
    key = f"{origin}→{dest}"
    if key in ROUTES:
        return ROUTES[key]

    # 模糊匹配
    for k, v in ROUTES.items():
        if origin in k and dest in k:
            return v

    # 默认用第一条
    return next(iter(ROUTES.values()), None)


@app.get("/health")
def health(): return {"ok": True, "agent": NAME}

@app.get("/meta")
def meta():
    return {
        "name": NAME, "version": "0.1.0", "skill": "shipping_quote",
        "description": "货代 Agent：持有海运运价数据库 (中国→欧洲各航线)",
        "routes_available": list(ROUTES.keys()),
    }

@app.post("/v1/route/list")
async def list_routes():
    return JSONResponse({"routes": [
        {"name": k, **v} for k, v in ROUTES.items()
    ]})

@app.post("/v1/shipping/quote")
async def shipping_quote(req: Request):
    """物流报价"""
    body = await req.json()
    product_name = (body or {}).get("product", "")
    qty = int((body or {}).get("qty", 100))
    dest = (body or {}).get("dest", "汉堡")

    # 支持直接传入产品信息（避免跨 daemon 调用）
    product_data = (body or {}).get("product_info")

    if not product_data:
        # 调供应商 Agent 获取产品重量/尺寸
        try:
            with SvcClient(base_url=ANET_BASE_URL) as svc:
                peers = svc.discover(skill="product_info")
                if peers:
                    target = peers[0]
                    resp = svc.call(target["peer_id"], target["services"][0]["name"],
                                    "/v1/product/detail", method="POST",
                                    body={"product": product_name})
                    body_resp = resp.get("body") or {}
                    if isinstance(body_resp, dict) and "hs_code" in body_resp:
                        product_data = body_resp
        except Exception as e:
            print(f"[C] failed to call supplier: {e}", flush=True)

    if not product_data:
        return JSONResponse({"error": f"无法获取产品信息: {product_name}"})

    hs = product_data.get("hs_code", "").replace(".", "")
    weight_kg = float(product_data.get("weight_kg", 1))
    origin = product_data.get("origin", "深圳")

    # 匹配路线
    route = _pick_route(origin, dest)
    if not route:
        return JSONResponse({"error": f"暂无 {origin}→{dest} 的航线"})

    # 计算费用
    cbm = _estimate_cbm(weight_kg, qty)
    total_weight = weight_kg * qty

    # FCL vs LCL 判断
    if cbm >= 18:
        # 整箱
        use_fcl = True
        containers = max(1, round(cbm / 28))
        freight = route["fcl_40hq_usd"] * containers
        container_desc = f"{containers} × 40HQ"
    else:
        use_fcl = False
        freight = round(cbm * route["lcl_usd_per_cbm"], 2)
        container_desc = f"拼箱 LCL ({cbm} CBM)"

    # 附加费
    surcharge_list = []
    for key in HS_SURCHARGE_MAP.get(hs[:4], ["BAF", "CAF", "THC", "ETS"]):
        info = SURCHARGES.get(key)
        if info:
            surcharge_list.append({"name": info["name"], "rate": info["rate"]})

    total_surcharge_pct = 15 + 8  # BAF + CAF
    if any(s["name"] == "危险品附加费" for s in surcharge_list):
        total_surcharge_pct += 5

    surcharge_cost = round(freight * total_surcharge_pct / 100, 2)
    total = round(freight + surcharge_cost, 2)

    return JSONResponse({
        "product": product_name,
        "qty": qty,
        "total_weight_kg": total_weight,
        "estimated_cbm": cbm,
        "route": f"{origin} → {dest}",
        "port_origin": route["port_origin"],
        "port_dest": route["port_dest"],
        "transit_days": route["transit_days"],
        "shipping_method": "FCL 整箱" if use_fcl else "LCL 拼箱",
        "container": container_desc if use_fcl else None,
        "freight_usd": freight,
        "surcharges": surcharge_list,
        "surcharge_total_usd": surcharge_cost,
        "total_usd": total,
        "cost_per_unit_usd": round(total / qty, 2),
        "note": "运价有效期 7-15 天，旺季可能上浮 40-100%。不含目的港清关和内陆派送费",
    })


def main():
    threading.Thread(
        target=lambda: register_agent(
            NAME, PORT,
            paths=["/v1/route/list", "/v1/shipping/quote", "/health", "/meta"],
            tags=["shipping_quote", "logistics", "trade"],
            description="货代 Agent：海运运价数据库 (中国→欧洲各港口 2025-2026)",
            per_call=PER_CALL,
        ), daemon=True,
    ).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

if __name__ == "__main__":
    main()
