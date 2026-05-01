"""Agent B — 合规顾问 (Compliance). 持有法规数据库 context + compliance_check skill."""

import os
import re
import threading
from typing import Optional
import uvicorn
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from anet.svc import SvcClient
from register import register_agent

NAME = "compliance-eu"
PORT = int(os.environ.get("AGENT_B_PORT", "7412"))
PER_CALL = int(os.environ.get("AGENT_B_PER_CALL", "0"))
ANET_BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13922")

app = FastAPI(title=NAME)

# ========== Context: 欧盟法规知识库 (2025-2026 真实数据) ==========
REGULATIONS = {
    "CE": {
        "name": "CE 标志 (强制)",
        "applies_to": ["电子产品", "玩具", "机械", "个人防护"],
        "description": "进入欧盟市场的基本安全认证。2025-2026 新规：RED 指令网络安全强制(EN 18031)，GPSR 全面执行",
        "cost_estimate": "认证费 ¥5,000-30,000 视产品复杂度",
        "timeline": "4-8 周",
    },
    "RoHS": {
        "name": "RoHS 2.0 (强制)",
        "applies_to": ["电子电气设备", "含电子元件的玩具", "家电"],
        "description": "管控 10 项有害物质（铅、汞、镉、六价铬、PBB、PBDE + 4 种邻苯）",
        "cost_estimate": "检测费 ¥2,000-5,000/产品",
        "timeline": "2-3 周",
    },
    "REACH": {
        "name": "REACH 法规 (强制)",
        "applies_to": ["所有化学品", "含化学品的成品", "纺织品", "玩具"],
        "description": "SVHC 候选清单截至 2026 年已达 255 项，持续增长中",
        "cost_estimate": "注册费 ¥10,000-50,000+/年",
        "timeline": "3-6 个月",
    },
    "UN38.3": {
        "name": "UN 38.3 (强制)",
        "applies_to": ["含锂电池产品", "锂电池单独运输"],
        "description": "锂电池运输安全测试，空运海运均需提供",
        "cost_estimate": "检测费 ¥3,000-8,000",
        "timeline": "2-4 周",
    },
    "CBAM": {
        "name": "碳边境调节机制 CBAM (强制)",
        "applies_to": ["钢铁", "铝", "水泥", "化肥", "氢能", "电力"],
        "description": "2026 年 1 月 1 日正式征收。需申报产品隐含碳排放 → 购买 CBAM 证书",
        "cost_estimate": "碳排放成本约 €30-50/吨 CO₂，默认值可能增加 30-50% 成本",
        "timeline": "持续合规，每年 9 月 30 日结算",
    },
    "TSR": {
        "name": "玩具安全法规 TSR (强制)",
        "applies_to": ["玩具", "儿童用品"],
        "description": "2026 年 1 月 1 日生效，2030 年取代旧指令。全面禁止 PFAS，甲醛限值收紧，需数字产品护照",
        "cost_estimate": "认证费 ¥10,000-50,000 + DPP 系统费",
        "timeline": "8-16 周",
    },
    "PFAS": {
        "name": "PFAS 禁令 (强制)",
        "applies_to": ["纺织品", "服装", "鞋类", "厨具", "电子产品涂层"],
        "description": "法国 2026.1.1、丹麦 2026.7.1 相继禁止含 PFAS 产品。EN 17826:2025 新增重金属和阻燃剂管控",
        "cost_estimate": "替代材料成本 +10-30%",
        "timeline": "需立即排查供应链",
    },
    "EUDR": {
        "name": "零毁林法案 EUDR (强制)",
        "applies_to": ["橡胶", "轮胎", "家具", "木材制品", "皮革"],
        "description": "2025.12.30 起大中型企业强制，2026.6.30 中小微企业宽限期截止。中国为低风险国家（利好）",
        "cost_estimate": "尽职调查系统搭建费 ¥20,000-100,000",
        "timeline": "2-3 个月准备",
    },
    "PPWR": {
        "name": "包装与包装废弃物法规 (强制)",
        "applies_to": ["所有产品的包装", "防尘袋", "衣架", "吊牌", "标签"],
        "description": "2026.8.12 起重金属总量 ≤100mg/kg，PFAS 严格限值。2030 年起包装须达可回收等级 A/B/C",
        "cost_estimate": "包装改造费 ¥5,000-30,000",
        "timeline": "按品类分阶段执行",
    },
    "MSDS": {
        "name": "化学品安全技术说明书 (强制)",
        "applies_to": ["锂电池", "化学品", "危险品"],
        "description": "出口化学品和含危险品的成品需提供多语言 MSDS",
        "cost_estimate": "编制费 ¥1,000-3,000/语种",
        "timeline": "1-2 周",
    },
    "EN71": {
        "name": "EN71 玩具安全标准 (强制)",
        "applies_to": ["玩具", "儿童用品"],
        "description": "欧盟玩具安全协调标准，含物理/化学/可燃性/电气测试",
        "cost_estimate": "检测费 ¥5,000-15,000",
        "timeline": "3-6 周",
    },
}

# HS 代码映射到适用法规
HS_REG_MAP = {
    "8711": ["CE", "RoHS", "REACH", "UN38.3"],
    "8518": ["CE", "RoHS", "REACH"],
    "8507": ["CE", "RoHS", "UN38.3", "MSDS", "CBAM"],
    "9503": ["CE", "TSR", "EN71", "REACH", "RoHS"],
    "9506": ["CE", "REACH"],
    "6100": ["PFAS", "REACH"],
    "6200": ["PFAS", "REACH"],
    "6400": ["PFAS", "REACH"],
    "9401": ["EUDR", "REACH"],
    "9403": ["EUDR", "REACH"],
    "4011": ["EUDR", "CE"],
}


def _find_regs(product_data: dict) -> list[dict]:
    """根据产品数据查找适用法规"""
    hs = product_data.get("hs_code", "").replace(".", "")
    cert_have = product_data.get("cert_have", [])
    cert_missing = product_data.get("cert_missing", [])

    # 通过 HS code 前 4 位匹配
    matched_keys = set()
    for prefix, regs in HS_REG_MAP.items():
        if hs.startswith(prefix):
            matched_keys.update(regs)

    # 加上缺失证书对应的法规
    for m in cert_missing:
        if m in REGULATIONS:
            matched_keys.add(m)

    results = []
    for key in sorted(matched_keys):
        reg = REGULATIONS.get(key, {})
        have = key in cert_have
        results.append({
            "regulation": key,
            "name": reg.get("name", key),
            "status": "✅ 已具备" if have else "❌ 需要办理",
            "description": reg.get("description", ""),
            "cost_estimate": reg.get("cost_estimate", ""),
            "timeline": reg.get("timeline", ""),
        })
    return results


@app.get("/health")
def health(): return {"ok": True, "agent": NAME}

@app.get("/meta")
def meta():
    return {
        "name": NAME, "version": "0.1.0", "skill": "compliance_check",
        "description": "合规顾问：持有欧盟法规数据库 (CBAM/RoHS/REACH/PFAS/EUDR/TSR…)",
        "regulations_covered": list(REGULATIONS.keys()),
    }

@app.post("/v1/regulation/list")
async def list_regulations():
    """列出所有法规"""
    return JSONResponse({"regulations": [
        {"key": k, "name": v["name"], "applies_to": v["applies_to"]}
        for k, v in REGULATIONS.items()
    ]})

@app.post("/v1/compliance/check")
async def compliance_check(req: Request):
    """检查产品需满足的法规要求"""
    body = await req.json()

    # 支持直接从参数传入产品信息，也可以调供应商 Agent 获取
    product_data = (body or {}).get("product_info")
    product_name = (body or {}).get("product", "")

    if not product_data and product_name:
        # 调供应商 Agent 获取产品详情
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
            print(f"[B] failed to call supplier: {e}", flush=True)

    if not product_data:
        return JSONResponse({"error": "需要 product_info 或 product 名称来查询供应商"})

    regs = _find_regs(product_data)
    total_cost_est = 0
    for r in regs:
        if r["status"] == "❌ 需要办理":
            nums = re.findall(r'[\d,]+', r["cost_estimate"])
            if nums:
                total_cost_est += int(nums[0].replace(",", ""))

    return JSONResponse({
        "product": product_data.get("product", product_name),
        "hs_code": product_data.get("hs_code", ""),
        "compliance_status": "⚠️ 待完善" if any(r["status"] == "❌ 需要办理" for r in regs) else "✅ 合规",
        "regulations": regs,
        "estimated_compliance_cost_cny": total_cost_est,
        "note": "以上法规要求基于 2025-2026 年欧盟最新规定，建议以第三方机构最终检测为准",
    })


def main():
    threading.Thread(
        target=lambda: register_agent(
            NAME, PORT,
            paths=["/v1/regulation/list", "/v1/compliance/check", "/health", "/meta"],
            tags=["compliance_check", "regulatory", "trade"],
            description="合规顾问 Agent：欧盟法规数据库 (RoHS/REACH/CBAM/PFAS/TSR/EUDR 等)",
            per_call=PER_CALL,
        ), daemon=True,
    ).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")

if __name__ == "__main__":
    main()
