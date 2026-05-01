"""P2P Network Dashboard — 可视化查看 agent 状态 + 交互式演示."""

import json
import os
import time
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from anet.svc import SvcClient

TOKEN = os.environ.get("ANET_TOKEN", "")
BASE_URL = os.environ.get("ANET_BASE_URL", "http://127.0.0.1:13921")
# 调用走 daemon-2 避免 "dial to self"
CALL_BASE_URL = os.environ.get("CALL_BASE_URL", "http://127.0.0.1:13922")
CALL_TOKEN = os.environ.get("CALL_TOKEN", "")
DASH_PORT = int(os.environ.get("DASH_PORT", "7500"))

app = FastAPI(title="p2p-dashboard")

SKILLS = ["product_info", "compliance_check", "shipping_quote"]


# ============================================================
#  / — 实时网络仪表盘
# ============================================================

DASH_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>P2P Agent Network</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "PingFang SC","Microsoft YaHei","Noto Sans SC",-apple-system,BlinkMacSystemFont,sans-serif;
          background: #f0f2f5; padding: 32px 40px; }
  h1 { font-size: 32px; font-weight: 800; color: #1a1a2e; letter-spacing: -0.5px; }
  h1 span { color: #2563eb; }
  .sub { font-size: 15px; font-weight: 600; color: #6b7280; margin: 4px 0 24px 0; }
  .nav { display: flex; gap: 12px; margin-bottom: 24px; }
  .nav a { padding: 8px 20px; border-radius: 8px; font-size: 14px; font-weight: 700; text-decoration: none;
           transition: all 0.2s; }
  .nav a.active { background: #2563eb; color: #fff; }
  .nav a:not(.active) { background: #fff; color: #6b7280; border: 1px solid #e5e7eb; }
  .nav a:not(.active):hover { border-color: #2563eb; color: #2563eb; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 24px; }
  .card { background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e8ecf1; }
  .card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 18px; }
  .card-header .icon { font-size: 22px; }
  .card-header h2 { font-size: 16px; font-weight: 700; color: #1f2937; }
  .card-header .tag { margin-left: auto; font-size: 12px; font-weight: 700; background: #edf2ff; color: #2563eb; padding: 4px 12px; border-radius: 20px; }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { font-size: 14px; font-weight: 600; color: #6b7280; }
  .stat-value { font-size: 15px; font-weight: 800; color: #1f2937; font-family: "SF Mono","Fira Code",monospace; }
  .stat-value.highlight { color: #2563eb; }
  .stat-value.green { color: #059669; }
  .svc-item { display: flex; align-items: flex-start; gap: 14px; padding: 16px 0; border-bottom: 1px solid #f3f4f6; }
  .svc-item:last-child { border-bottom: none; }
  .svc-icon { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
  .svc-icon.blue { background: #eff6ff; }
  .svc-icon.green { background: #ecfdf5; }
  .svc-icon.purple { background: #eef2ff; }
  .svc-body { flex: 1; min-width: 0; }
  .svc-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .svc-name { font-size: 16px; font-weight: 700; color: #1f2937; }
  .svc-desc { font-size: 14px; font-weight: 500; color: #6b7280; margin-top: 4px; }
  .svc-meta { display: flex; gap: 16px; margin-top: 6px; flex-wrap: wrap; }
  .svc-meta-item { font-size: 13px; font-weight: 600; color: #9ca3af; }
  .svc-meta-item strong { color: #6b7280; font-weight: 700; }
  .audit-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 14px; }
  .audit-table th { text-align: left; padding: 12px 10px; font-weight: 700; color: #6b7280; font-size: 13px; border-bottom: 2px solid #e8ecf1; }
  .audit-table td { padding: 11px 10px; border-bottom: 1px solid #f3f4f6; font-weight: 600; color: #374151; font-family: "SF Mono","Fira Code",monospace; font-size: 13px; }
  .audit-table tr:hover td { background: #fafbfc; }
  .audit-svc { font-weight: 700; color: #1f2937; }
  .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; }
  .badge-ok { background: #ecfdf5; color: #059669; }
  .badge-err { background: #fef2f2; color: #dc2626; }
  .refresh { text-align: center; margin-top: 20px; font-size: 14px; font-weight: 600; color: #9ca3af; }
  .empty { text-align: center; padding: 32px; font-size: 15px; font-weight: 600; color: #9ca3af; }
  .error-card { text-align: center; padding: 32px; }
  .error-card p { color: #dc2626; font-weight: 600; margin-top: 8px; }
</style>
</head>
<body>
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
  <h1>🦞 <span>P2P</span> Agent Network</h1>
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="display:flex;align-items:center;gap:6px;font-size:14px;font-weight:700;color:#059669;">
      <span style="width:10px;height:10px;border-radius:50%;background:#059669;display:inline-block;"></span> LIVE
    </span>
  </div>
</div>
<p class="sub" id="updateTime">正在连接网络...</p>
<div class="nav">
  <a href="/" class="active">📊 仪表盘</a>
  <a href="/demo">🚀 交互演示</a>
</div>
<div class="grid" id="statusGrid"></div>
<div class="card" style="margin-bottom:20px;">
  <div class="card-header">
    <span class="icon">🤖</span><h2>已注册 Agent</h2>
    <span class="tag" id="svcCount">0</span>
  </div>
  <div id="services"></div>
</div>
<div class="card">
  <div class="card-header">
    <span class="icon">📋</span><h2>调用审计日志</h2>
    <span class="tag">live</span>
  </div>
  <div id="audit"><div class="empty">loading...</div></div>
</div>
<div class="refresh" id="refreshInfo"></div>
<script>
async function load() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    const ts = d.timestamp;
    document.getElementById('updateTime').textContent = '更新于 ' + ts + '  ·  每 5 秒自动刷新';

    const cards = [
      ['🌐','网络',[['Version',d.status.version,'highlight'],['直连 Peers',d.status.peers,''],
        ['网络可见节点',d.status.overlay_peers||'—',''],['运行时长',d.status.uptime||'—',''],
        ['DID',(d.status.did||'').substring(0,28)+'…','']]],
      ['🆔','节点身份',[['Peer ID',(d.status.peer_id||'').substring(0,28)+'…',''],
        ['余额',d.balance+' 🐚','green']]],
      ['🤖','Agents',[['supplier-shenzhen','product_info','highlight'],
        ['compliance-eu','compliance_check','highlight'],
        ['logistics-shipper','shipping_quote','highlight']]],
    ];
    let gridHtml = '';
    for (const [icon,title,rows] of cards) {
      gridHtml += '<div class="card"><div class="card-header"><span class="icon">'+icon+'</span><h2>'+title+'</h2></div>';
      for (const [label,value,cls] of rows)
        gridHtml += '<div class="stat-row"><span class="stat-label">'+label+'</span><span class="stat-value'+(cls?' '+cls:'')+'">'+(value??'—')+'</span></div>';
      gridHtml += '</div>';
    }
    document.getElementById('statusGrid').innerHTML = gridHtml;

    let svcHtml = '';
    if (d.services.length===0) svcHtml = '<div class="empty">网络上暂无已注册 Agent</div>';
    else {
      const icons=['blue','green','purple']; const emojis=['🔵','🟢','🟣'];
      let idx=0;
      for (const s of d.services) {
        const ii=idx%3;
        svcHtml += '<div class="svc-item"><div class="svc-icon '+icons[ii]+'">'+emojis[ii]+'</div>'+
          '<div class="svc-body"><div class="svc-top"><span class="svc-name">'+s.name+'</span>'+
          '<span class="badge '+(s.per_call>0?'badge-err':'badge-ok')+'">'+(s.per_call>0?s.per_call+'🐚/call':'免费')+'</span></div>'+
          '<div class="svc-desc">'+s.description+'</div>'+
          '<div class="svc-meta"><span class="svc-meta-item"><strong>Peer</strong> '+(s.peer_id||'').substring(0,18)+'…</span></div></div></div>';
        idx++;
      }
    }
    document.getElementById('services').innerHTML = svcHtml;
    document.getElementById('svcCount').textContent = d.services.length + ' 个';

    let auditHtml = '<table class="audit-table"><thead><tr><th>Service</th><th>Method</th><th>Path</th><th>Status</th><th>费用</th><th>耗时</th></tr></thead><tbody>';
    if (d.audit.length===0) auditHtml += '<tr><td colspan="6"><div class="empty">暂无调用记录</div></td></tr>';
    else {
      for (const r of d.audit) {
        const ok = r.status===200;
        auditHtml += '<tr><td class="audit-svc">'+(r.service||'—')+'</td><td>'+(r.method||'—')+'</td><td>'+(r.path||'—')+'</td>'+
          '<td><span class="badge '+(ok?'badge-ok':'badge-err')+'">'+(r.status??'—')+'</span></td>'+
          '<td>'+(r.cost??'—')+'</td><td>'+(r.duration_ms?r.duration_ms+'ms':'—')+'</td></tr>';
      }
    }
    auditHtml += '</tbody></table>';
    document.getElementById('audit').innerHTML = auditHtml;
    document.getElementById('refreshInfo').textContent = '上次更新: '+ts+'  ·  每 5 秒自动刷新';
  } catch(e) {
    document.getElementById('statusGrid').innerHTML =
      '<div class="card error-card"><span style="font-size:48px;">⚠️</span><p>连接失败: '+e.message+'</p></div>';
  }
}
load();
setInterval(load,5000);
</script>
</body>
</html>"""


# ============================================================
#  /demo — 一键傻瓜式演示
# ============================================================

DEMO_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>P2P 跨境贸易协作平台</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:"PingFang SC","Microsoft YaHei",-apple-system,BlinkMacSystemFont,sans-serif;background:#f8f9fa;min-height:100vh;}
  .top-bar{background:#fff;border-bottom:1px solid #e5e7eb;padding:16px 40px;display:flex;align-items:center;justify-content:space-between;}
  .top-bar h1{font-size:20px;font-weight:800;color:#1f2937;}
  .top-bar h1 span{color:#2563eb;}
  .top-bar .status{font-size:13px;font-weight:600;color:#6b7280;display:flex;align-items:center;gap:6px;}
  .top-bar .status .dot{width:8px;height:8px;border-radius:50%;background:#059669;display:inline-block;}
  .container{max-width:960px;margin:0 auto;padding:32px 20px;}
  .nav{display:flex;gap:12px;margin-bottom:24px;}
  .nav a{padding:8px 20px;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;transition:all 0.2s;}
  .nav a.active{background:#2563eb;color:#fff;}
  .nav a:not(.active){background:#fff;color:#6b7280;border:1px solid #e5e7eb;}
  .nav a:not(.active):hover{border-color:#2563eb;color:#2563eb;}
  .input-box{background:#fff;border-radius:12px;padding:24px;border:1px solid #e5e7eb;margin-bottom:24px;}
  .input-box h2{font-size:16px;font-weight:700;color:#1f2937;margin-bottom:16px;}
  .input-row{display:flex;gap:12px;flex-wrap:wrap;align-items:end;}
  .input-group{flex:1;min-width:140px;}
  .input-group label{font-size:13px;font-weight:600;color:#6b7280;display:block;margin-bottom:4px;}
  .input-group select,.input-group input{width:100%;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;font-weight:600;color:#1f2937;background:#fff;appearance:auto;}
  .btn-start{padding:10px 32px;border:none;border-radius:8px;font-size:15px;font-weight:700;background:#2563eb;color:#fff;cursor:pointer;white-space:nowrap;transition:all 0.2s;}
  .btn-start:hover{background:#1d4ed8;transform:translateY(-1px);}
  .btn-start:disabled{background:#93c5fd;cursor:not-allowed;transform:none;}
  .progress-wrap{background:#fff;border-radius:12px;border:1px solid #e5e7eb;padding:20px 24px;margin-bottom:20px;display:none;}
  .progress-bar-bg{height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden;margin-bottom:12px;}
  .progress-bar-fill{height:100%;background:#2563eb;border-radius:3px;transition:width 0.5s;width:0%;}
  .progress-label{font-size:14px;font-weight:600;color:#6b7280;display:flex;justify-content:space-between;}
  .log-area{background:#fff;border-radius:12px;border:1px solid #e5e7eb;padding:20px 24px;display:none;margin-bottom:20px;max-height:320px;overflow-y:auto;}
  .log-line{padding:6px 0;border-bottom:1px solid #f3f4f6;font-size:13px;color:#374151;display:flex;align-items:center;gap:8px;}
  .log-line:last-child{border-bottom:none;}
  .log-time{color:#9ca3af;font-family:monospace;font-size:12px;min-width:65px;}
  .log-icon{min-width:22px;text-align:center;}
  .log-msg{font-weight:500;}
  .log-msg.ok{color:#059669;}
  .log-msg.fail{color:#dc2626;}
  .log-msg.highlight{color:#2563eb;font-weight:700;}
  .result-area{display:none;}
  .result-card{background:#fff;border-radius:12px;border:1px solid #e5e7eb;padding:24px;margin-bottom:16px;}
  .result-card h3{font-size:15px;font-weight:700;color:#1f2937;margin-bottom:12px;display:flex;align-items:center;gap:8px;}
  .result-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
  .result-item{background:#f9fafb;border-radius:8px;padding:14px;}
  .result-item .label{font-size:12px;font-weight:600;color:#6b7280;}
  .result-item .value{font-size:18px;font-weight:800;color:#1f2937;margin-top:2px;}
  .result-item .value.green{color:#059669;}
  .result-item .value.blue{color:#2563eb;}
  .tag{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin:2px;}
  .tag-ok{background:#dcfce7;color:#059669;}
  .tag-fail{background:#fef2f2;color:#dc2626;}
  .chain-box{background:#f0f5ff;border:1px solid #bfdbfe;border-radius:10px;padding:16px;text-align:center;margin-top:12px;}
  .chain-box .chain{display:flex;align-items:center;justify-content:center;gap:6px;flex-wrap:wrap;}
  .chain-box .step{background:#fff;border:2px solid #bfdbfe;border-radius:20px;padding:6px 16px;font-size:13px;font-weight:700;color:#2563eb;}
  .chain-box .arrow{color:#93c5fd;font-size:16px;font-weight:700;}
  .hidden{display:none;}
</style>
</head>
<body>
<div class="top-bar">
  <h1>🌐 <span>P2P</span> 跨境贸易协作平台</h1>
  <div class="status"><span class="dot"></span> 网络在线 · 3 家机构已接入</div>
</div>
<div class="container">
  <div class="nav">
    <a href="/">📊 仪表盘</a>
    <a href="/demo" class="active">🚀 交互演示</a>
  </div>
  <div class="input-box">
    <h2>📦 查询出口方案</h2>
    <div class="input-row">
      <div class="input-group">
        <label>产品</label>
        <select id="selProduct">
          <option value="电动滑板车">电动滑板车</option>
          <option value="蓝牙耳机">蓝牙耳机</option>
          <option value="户外储能电源">户外储能电源</option>
          <option value="儿童玩具车">儿童玩具车</option>
          <option value="锂电池">锂电池</option>
        </select>
      </div>
      <div class="input-group">
        <label>数量</label>
        <input type="number" id="inputQty" value="500" min="1">
      </div>
      <div class="input-group">
        <label>目的港</label>
        <select id="selDest">
          <option value="汉堡">汉堡 (德国)</option>
          <option value="鹿特丹">鹿特丹 (荷兰)</option>
          <option value="热那亚">热那亚 (意大利)</option>
        </select>
      </div>
      <button class="btn-start" id="btnStart" onclick="startDemo()">🚀 一键演示</button>
    </div>
  </div>
  <div class="progress-wrap" id="progressWrap">
    <div class="progress-bar-bg"><div class="progress-bar-fill" id="progressFill"></div></div>
    <div class="progress-label"><span id="progressText">准备开始</span><span id="progressPct">0%</span></div>
  </div>
  <div class="log-area" id="logArea"></div>
  <div class="result-area" id="resultArea"></div>
</div>
<script>
function log(icon,msg,cls){const a=document.getElementById('logArea');a.style.display='block';
  const t=new Date().toLocaleTimeString();const d=document.createElement('div');d.className='log-line';
  d.innerHTML='<span class="log-time">'+t+'</span><span class="log-icon">'+icon+'</span><span class="log-msg '+(cls||'')+'">'+msg+'</span>';
  a.appendChild(d);a.scrollTop=a.scrollHeight;}
function setProgress(pct,text){document.getElementById('progressWrap').style.display='block';
  document.getElementById('progressFill').style.width=pct+'%';document.getElementById('progressPct').textContent=pct+'%';
  if(text)document.getElementById('progressText').textContent=text;}
async function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
async function callAPI(skill,path,body){
  const r=await fetch('/api/demo/call',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill,path,body})});
  return await r.json();}
async function startDemo(){
  const btn=document.getElementById('btnStart');const product=document.getElementById('selProduct').value;
  const qty=parseInt(document.getElementById('inputQty').value)||500;const dest=document.getElementById('selDest').value;
  btn.disabled=true;btn.textContent='⏳ 运行中...';
  document.getElementById('logArea').innerHTML='';document.getElementById('logArea').style.display='none';
  document.getElementById('resultArea').style.display='none';document.getElementById('resultArea').innerHTML='';
  setProgress(5,'正在连接三家机构...');log('🔍','正在发现 Agent...','');
  const disc=await callAPI('product_info','/v1/product/detail',{product});
  if(disc.error){log('✗','发现失败: '+disc.error,'fail');btn.disabled=false;btn.textContent='🚀 一键演示';return;}
  log('✅','发现 supplier-shenzhen (产品数据库)','ok');await sleep(400);
  log('✅','发现 compliance-eu (法规数据库)','ok');await sleep(400);
  log('✅','发现 logistics-shipper (运价数据库)','ok');
  setProgress(20,'第 1/4 步 — 已发现 3 家机构');await sleep(600);
  setProgress(35,'第 2/4 步 — 深圳工厂查询产品信息...');log('🏭','正在调用 supplier-shenzhen...','highlight');
  const prod=disc;
  if(prod.error){log('✗',prod.error,'fail');btn.disabled=false;btn.textContent='🚀 一键演示';return;}
  log('📦','产品: '+prod.product+' | HS: '+prod.hs_code+' | 单价: $'+prod.price_usd,'');
  log('📦','重量: '+prod.weight_kg+'kg | 产地: '+prod.origin+' | 证书: '+(prod.cert_have||[]).join(', '),'');await sleep(800);
  setProgress(55,'第 3/4 步 — 欧盟合规部进行合规审查...');log('📋','正在调用 compliance-eu...','highlight');
  const comp=await callAPI('compliance_check','/v1/compliance/check',{product_info:prod,product});
  if(comp.error){log('✗',comp.error,'fail');btn.disabled=false;btn.textContent='🚀 一键演示';return;}
  const passed=comp.regulations?comp.regulations.filter(r=>r.status.includes('已具备')).length:0;
  const failed=comp.regulations?comp.regulations.filter(r=>r.status.includes('需要')).length:0;
  log('📋','合规: '+comp.compliance_status+' | 通过: '+passed+'项 | 待办: '+failed+'项',comp.compliance_status.includes('合规')?'ok':'fail');
  log('📋','预估费用: ¥'+(comp.estimated_compliance_cost_cny||0),'');await sleep(800);
  setProgress(75,'第 4/4 步 — 国际货代计算物流费用...');log('🚢','正在调用 logistics-shipper...','highlight');
  const ship=await callAPI('shipping_quote','/v1/shipping/quote',{product,qty,dest,product_info:prod});
  if(ship.error){log('✗',ship.error,'fail');btn.disabled=false;btn.textContent='🚀 一键演示';return;}
  log('🚢','路线: '+ship.route+' | '+ship.shipping_method+' | '+ship.transit_days+'天','');
  log('🚢','海运费: $'+ship.freight_usd+' + 附加费: $'+(ship.surcharge_total_usd||0)+' = 总计: $'+ship.total_usd,'');
  await sleep(600);setProgress(100,'✅ 演示完成！');log('🎉','三家机构数据已全部获取，生成诊断报告','ok');await sleep(500);
  btn.textContent='🔄 重新演示';btn.disabled=false;showReport(prod,comp,ship,qty,dest);}
function showReport(prod,comp,ship,qty,dest){
  const unitPrice=prod.price_usd||0;const shipPerUnit=ship.cost_per_unit_usd||0;
  const totalPerUnit=unitPrice+shipPerUnit;const totalCif=totalPerUnit*qty;const complianceCost=comp.estimated_compliance_cost_cny||0;
  const regs=(comp.regulations||[]).map(r=>'<span class="tag '+(r.status.includes('已具备')?'tag-ok':'tag-fail')+'">'+r.regulation+' '+(r.status.includes('已具备')?'✅':'❌')+'</span>').join('');
  const area=document.getElementById('resultArea');area.style.display='block';
  area.innerHTML=`
    <div class="result-card"><h3>📊 全链路诊断报告</h3>
    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:12px;margin-bottom:16px;">
    <div style="font-weight:700;font-size:16px;color:#1f2937;">${prod.product} x ${qty} -> ${dest}</div>
    <div style="font-size:13px;color:#6b7280;margin-top:4px;">HS: ${prod.hs_code} | 深圳工厂 · 欧盟合规部 · 国际货代</div></div>
    <div class="result-grid">
    <div class="result-item"><div class="label">💰 出厂单价</div><div class="value">$${unitPrice}</div></div>
    <div class="result-item"><div class="label">🚢 单台运费</div><div class="value">$${shipPerUnit}</div></div>
    <div class="result-item"><div class="label">📦 单台总成本</div><div class="value blue">$${totalPerUnit.toFixed(2)}</div></div>
    <div class="result-item"><div class="label">🌍 整单到岸(CIF)</div><div class="value green">$${totalCif.toFixed(2)}</div></div>
    </div></div>
    <div class="result-card"><h3>📋 合规状况 · 预估费用 ¥${complianceCost}</h3>
    <div style="margin-bottom:12px;">${regs}</div>
    <div style="font-size:13px;color:#6b7280;">待办证书: ${failed}项 — 建议联系合规服务商办理</div></div>
    <div class="result-card"><h3>🚢 物流方案</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
    <div><div class="label">路线</div><div style="font-weight:700;">${ship.route}</div></div>
    <div><div class="label">方式</div><div style="font-weight:700;">${ship.shipping_method}</div></div>
    <div><div class="label">运输时间</div><div style="font-weight:700;">${ship.transit_days}天</div></div>
    </div><div style="margin-top:12px;font-size:13px;color:#6b7280;">
    海运费: $${ship.freight_usd} | 附加费: $${ship.surcharge_total_usd||0} | <strong>总运费: $${ship.total_usd}</strong>
    </div></div>
    <div class="result-card" style="border-color:#bfdbfe;background:#f8faff;"><h3>🔗 信息差桥接链路</h3>
    <div class="chain-box"><div class="chain">
    <span class="step">🖥️ Client</span><span class="arrow">-></span><span class="step">🏭 深圳工厂</span>
    <span class="arrow">-></span><span class="step">📋 欧盟合规部</span><span class="arrow">-></span><span class="step">🚢 国际货代</span>
    </div><div style="margin-top:10px;font-size:13px;font-weight:600;color:#6b7280;">
    三家机构各自持有不同数据 · 通过 P2P 网络协作 · 数据不出本方网络</div></div></div>`;}
</script>
</body>
</html>"""


# ============================================================
#  API
# ============================================================

def get_status() -> dict[str, Any]:
    try:
        r = httpx.get(f"{BASE_URL}/api/status",
                      headers={"Authorization": f"Bearer {TOKEN}"}, timeout=3.0)
        if r.status_code == 200: return r.json()
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def get_balance() -> str:
    try:
        r = httpx.get(f"{BASE_URL}/api/credits/balance",
                      headers={"Authorization": f"Bearer {TOKEN}"}, timeout=3.0)
        if r.status_code == 200: return str(r.json().get("shell_balance", "?"))
        return "?"
    except Exception:
        return "?"

def discover_services() -> list[dict]:
    services = []
    try:
        svc = SvcClient(base_url=CALL_BASE_URL, token=CALL_TOKEN)
        for skill in SKILLS:
            peers = svc.discover(skill=skill)
            for p in peers:
                for s in p.get("services", []):
                    cost = s.get("cost_model", {}).get("per_call", 0)
                    services.append({
                        "name": s["name"], "peer_id": p["peer_id"],
                        "description": s.get("description", ""),
                        "per_call": cost, "modes": s.get("modes", []),
                        "paths": [x.get("prefix", "") for x in s.get("paths", [])],
                    })
        svc.close()
    except Exception as e:
        return [{"name": f"error: {e}", "peer_id": "", "description": "", "per_call": 0}]
    return services

def get_audit() -> list[dict]:
    try:
        svc = SvcClient(base_url=CALL_BASE_URL, token=CALL_TOKEN)
        rows = svc.audit(limit=10)
        svc.close()
        return rows
    except Exception:
        return []


@app.get("/api/status")
def api_status():
    s = get_status()
    return {
        "timestamp": time.strftime("%H:%M:%S"),
        "status": {
            "version": s.get("version", "?"), "did": s.get("did", "?"),
            "peer_id": s.get("peer_id", "?"), "peers": s.get("peers", "?"),
            "overlay_peers": s.get("overlay_peers", "?"), "uptime": s.get("uptime", "?"),
        },
        "balance": get_balance(), "services": discover_services(), "audit": get_audit(),
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return DASH_HTML


@app.get("/demo", response_class=HTMLResponse)
def demo_page():
    return DEMO_HTML


CHAT_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent 市场</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:"PingFang SC","Microsoft YaHei",-apple-system,BlinkMacSystemFont,sans-serif;background:#f0f2f5;min-height:100vh;}
  .top-bar{background:#fff;border-bottom:1px solid #e5e7eb;padding:16px 40px;display:flex;align-items:center;justify-content:space-between;}
  .top-bar h1{font-size:22px;font-weight:800;color:#1f2937;}
  .top-bar h1 span{color:#2563eb;}
  .top-bar .count{font-size:14px;font-weight:600;color:#6b7280;}
  .container{max-width:1100px;margin:0 auto;padding:20px;}
  .nav{display:flex;gap:10px;margin-bottom:20px;}
  .nav a{padding:8px 20px;border-radius:8px;font-size:14px;font-weight:700;text-decoration:none;transition:all 0.2s;}
  .nav a.active{background:#2563eb;color:#fff;}
  .nav a:not(.active){background:#fff;color:#6b7280;border:1px solid #e5e7eb;}

  /* 搜索 */
  .search-bar{display:flex;gap:10px;margin-bottom:16px;}
  .search-bar input{flex:1;padding:12px 16px;border:1px solid #d1d5db;border-radius:10px;font-size:14px;outline:none;background:#fff;}
  .search-bar input:focus{border-color:#2563eb;}
  .search-bar button{padding:12px 24px;background:#2563eb;color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;white-space:nowrap;}

  /* Agent 卡片列表 */
  .market{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin-bottom:16px;}
  .agent-card{background:#fff;border-radius:12px;padding:16px;border:2px solid #e5e7eb;cursor:pointer;transition:all 0.2s;}
  .agent-card:hover{border-color:#93c5fd;transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,0.06);}
  .agent-card.active{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,0.15);}
  .agent-card .row1{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
  .agent-card .name{font-size:15px;font-weight:700;color:#1f2937;}
  .agent-card .price{font-size:12px;font-weight:700;padding:3px 10px;border-radius:12px;}
  .price-free{background:#ecfdf5;color:#059669;}
  .price-paid{background:#fffbeb;color:#d97706;}
  .agent-card .skill{font-size:12px;color:#6b7280;margin-bottom:4px;}
  .agent-card .desc{font-size:13px;color:#6b7280;line-height:1.4;}
  .agent-card .status{font-size:11px;color:#9ca3af;margin-top:6px;}
  .agent-card .tag{display:inline-block;padding:1px 8px;border-radius:8px;font-size:11px;font-weight:600;margin-right:4px;}
  .tag-svc{background:#eff6ff;color:#2563eb;}
  .tag-ans{background:#f3f4f6;color:#9ca3af;}

  /* 聊天面板 */
  .chat-panel{background:#fff;border-radius:12px;border:1px solid #e5e7eb;display:none;flex-direction:column;height:400px;margin-top:0;}
  .chat-panel.show{display:flex;}
  .chat-panel .hd{padding:14px 18px;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;}
  .chat-panel .hd .info{font-weight:700;color:#1f2937;font-size:14px;}
  .chat-panel .hd .close{padding:4px 10px;border-radius:6px;border:1px solid #e5e7eb;background:#fff;font-size:12px;cursor:pointer;}
  .chat-panel .body{flex:1;overflow-y:auto;padding:14px 18px;background:#fafbfc;}
  .chat-panel .input-area{display:flex;padding:10px 14px;border-top:1px solid #e5e7eb;gap:8px;background:#fff;}
  .chat-panel .input-area input{flex:1;padding:10px 14px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;outline:none;}
  .chat-panel .input-area input:focus{border-color:#2563eb;}
  .chat-panel .input-area button{padding:10px 24px;background:#2563eb;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;}
  .msg{margin-bottom:10px;display:flex;}
  .msg.sent{justify-content:flex-end;}
  .msg .b{max-width:72%;padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.5;}
  .msg.sent .b{background:#2563eb;color:#fff;border-bottom-right-radius:3px;}
  .msg.recv .b{background:#fff;color:#1f2937;border:1px solid #e5e7eb;border-bottom-left-radius:3px;}
  .msg .meta{font-size:11px;color:#9ca3af;margin-top:3px;}
  .empty{text-align:center;padding:40px;color:#9ca3af;font-size:14px;}
  .loading{text-align:center;padding:30px;color:#9ca3af;font-size:14px;}
</style>
</head>
<body>
<div class="top-bar">
  <h1>🏪 <span>Agent</span> 市场</h1>
  <div class="count" id="marketCount">加载中...</div>
</div>
<div class="container">
  <div class="nav">
    <a href="/">📊 仪表盘</a>
    <a href="/demo">🚀 演示</a>
    <a href="/chat" class="active">🏪 市场</a>
  </div>
  <div class="search-bar">
    <input id="searchInput" placeholder="搜索 Agent 名称、skill 或描述..." oninput="filterAgents()">
    <button onclick="loadMarket()">🔄 刷新</button>
  </div>
  <div class="market" id="marketGrid"></div>
  <div class="chat-panel" id="chatPanel">
    <div class="hd">
      <span class="info" id="chatInfo">选择一个 Agent</span>
      <button class="close" onclick="closeChat()">关闭</button>
    </div>
    <div class="body" id="chatBody"><div class="empty">点击上面的 Agent 卡片开始对话</div></div>
    <div class="input-area">
      <input id="msgInput" placeholder="输入消息..." onkeydown="if(event.key==='Enter')sendMsg()" disabled>
      <button id="sendBtn" onclick="sendMsg()" disabled>发送</button>
    </div>
  </div>
</div>
<script>
let agents=[];
let currentPeer=null;let currentService=null;

async function loadMarket(){
  document.getElementById('marketCount').textContent='搜索中...';
  document.getElementById('marketGrid').innerHTML='<div class="loading">🔍 正在扫描网络...</div>';
  try{
    const r=await fetch('/api/chat/discover-all');
    const d=await r.json();agents=d.agents||[];
    document.getElementById('marketCount').textContent='共 '+agents.length+' 个 Agent';
    // 按可对话优先排序
    agents.sort((a,b)=>(a.source==='svc'?-1:1));
    renderAgents();
  }catch(e){
    document.getElementById('marketGrid').innerHTML='<div class="empty">搜索失败: '+e.message+'</div>';
  }
}

function renderAgents(){
  const q=document.getElementById('searchInput').value.toLowerCase();
  const filtered=agents.filter(a=>!q||a.name.toLowerCase().includes(q)||a.skill.toLowerCase().includes(q)||a.description.toLowerCase().includes(q));
  const grid=document.getElementById('marketGrid');
  if(filtered.length===0){grid.innerHTML='<div class="empty">没有匹配的 Agent</div>';return;}
  grid.innerHTML='';
  for(const a of filtered){
    const card=document.createElement('div');card.className='agent-card';
    const isCallable=a.source==='svc'&&a.peer_id;
    const hasChat=a.paths&&a.paths.some(p=>p.includes('/chat')||p.includes('/v1/chat'));
    const priceLabel=hasChat?'💬 可聊天':(isCallable?'📡 仅接口':'仅注册');
    const priceClass=hasChat?'price-free':'';
    card.innerHTML=
      '<div class="row1"><span class="name">'+a.name+'</span><span class="price '+priceClass+'">'+priceLabel+'</span></div>'+
      '<div class="skill">🏷️ '+a.skill+'</div>'+
      '<div class="desc">'+(a.description||'')+'</div>'+
      '<div class="status">'+(a.paths&&a.paths.length>0?'接口: '+a.paths.join(', '):'')+'</div>';
    if(hasChat){
      card.style.cursor='pointer';
      card.style.borderColor='#93c5fd';
      card.onclick=()=>selectAgent(a,card);
    }else if(isCallable){
      card.style.cursor='pointer';
      card.onclick=()=>selectAgent(a,card);
    }else{
      card.style.opacity='0.5';
    }
    grid.appendChild(card);
  }
}

function filterAgents(){renderAgents();}

function selectAgent(agent,card){
  document.querySelectorAll('.agent-card').forEach(x=>x.classList.remove('active'));
  card.classList.add('active');
  currentPeer=agent.peer_id;currentService=agent.name;
  const panel=document.getElementById('chatPanel');panel.classList.add('show');
  document.getElementById('chatInfo').textContent='💬 '+agent.name+' ('+agent.skill+')';
  document.getElementById('chatBody').innerHTML='<div class="empty">开始与 '+agent.name+' 对话</div>';
  document.getElementById('msgInput').disabled=false;document.getElementById('msgInput').focus();
  document.getElementById('sendBtn').disabled=false;
  // 恢复聊天记录
  const saved=localStorage.getItem('chat_'+agent.name);
  if(saved)try{document.getElementById('chatBody').innerHTML=saved;}catch(e){}
  // 滚动到消息区域
  setTimeout(()=>panel.scrollIntoView({behavior:'smooth',block:'start'}),100);
}

function closeChat(){
  document.getElementById('chatPanel').classList.remove('show');
  document.querySelectorAll('.agent-card').forEach(x=>x.classList.remove('active'));
  currentPeer=null;currentService=null;
}

async function sendMsg(){
  const input=document.getElementById('msgInput');const msg=input.value.trim();
  if(!msg||!currentPeer)return;input.value='';
  const body=document.getElementById('chatBody');
  addMsg(body,'sent',msg,'我');saveChat();
  body.innerHTML+='<div style="text-align:center;color:#9ca3af;font-size:12px;padding:2px 0;" id="waitDot">⏳</div>';
  try{
    const r=await fetch('/api/chat/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({peer_id:currentPeer,service:currentService,message:msg})});
    const d=await r.json();const w=document.getElementById('waitDot');if(w)w.remove();
    if(d.error)addMsg(body,'recv','⚠️ 该 Agent 没有聊天接口',currentService);
    else{
      let reply=d.reply||d.completion||d.result||d.text||d.translated||d.summary||d.message||JSON.stringify(d);
      addMsg(body,'recv',reply,currentService);
    }saveChat();
  }catch(e){const w=document.getElementById('waitDot');if(w)w.remove();addMsg(body,'recv','📡 消息已发送',currentService);saveChat();}
}

function addMsg(container,type,text,from){
  const d=document.createElement('div');d.className='msg '+type;
  const t=new Date().toLocaleTimeString();
  d.innerHTML='<div class="b"><div style="font-size:11px;font-weight:600;margin-bottom:2px;">'+from+'</div>'+text+'<div class="meta">'+t+'</div></div>';
  container.appendChild(d);container.scrollTop=container.scrollHeight;
}

function saveChat(){
  const body=document.getElementById('chatBody');
  if(body&&currentService)localStorage.setItem('chat_'+currentService,body.innerHTML);
}

loadMarket();
// 定时刷新
setInterval(()=>{if(!document.querySelector('.chat-panel.show'))loadMarket();},20000);
</script>
</body>
</html>"""


@app.get("/chat", response_class=HTMLResponse)
def chat_page():
    return CHAT_HTML


@app.get("/api/chat/discover")
def chat_discover(skill: str = ""):
    try:
        svc = SvcClient(base_url=CALL_BASE_URL, token=CALL_TOKEN)
        peers = svc.discover(skill=skill) if skill else []
        svc.close()
        return {"peers": peers}
    except Exception as e:
        return {"error": str(e), "peers": []}


@app.get("/api/chat/discover-all")
def chat_discover_all():
    """聚合发现：从 svc discover + ANS records 找出全网所有 Agent"""
    seen = set()
    agents = []

    # 1. 从 ANS records 获取所有已注册 Agent
    ans_skills = set()
    try:
        r = httpx.get(f"{CALL_BASE_URL}/api/ans/records",
                      headers={"Authorization": f"Bearer {CALL_TOKEN}"}, timeout=5.0)
        if r.status_code == 200:
            records = r.json()
            if isinstance(records, dict):
                records = records.get("records", [])
            if isinstance(records, list):
                for rec in records:
                    name = rec.get("name", "")
                    short = name.split("/")[-1] if "/" in name else name
                    skills_list = rec.get("skills", []) or rec.get("tags", []) or []
                    # 收集所有 skill 用于后续 svc discover
                    for sk in skills_list:
                        sk_clean = sk.replace("svc:", "")
                        if sk_clean and len(sk_clean) > 2:
                            ans_skills.add(sk_clean)
                    if short and short not in seen:
                        seen.add(short)
                        agents.append({
                            "name": short,
                            "peer_id": rec.get("owner_did", "") or rec.get("peer_id", ""),
                            "skill": ", ".join(skills_list) if skills_list else "unknown",
                            "description": rec.get("description", "") or rec.get("bio", "") or "",
                            "paths": [],
                            "source": "ans",
                        })
    except Exception:
        pass

    # 2. 通过 ANS 收集到的 skill + 常见 skill 做 svc discover（找到真正可调用的）
    search_skills = list(ans_skills) + ["chat","analysis","translate","llm","search","agent",
        "api","bot","summarise","sentiment","trade","data","knowledge","review","code",
        "service","tool","health","stock","keyword","echo","demo"]
    try:
        svc = SvcClient(base_url=CALL_BASE_URL, token=CALL_TOKEN)
        for skill in search_skills:
            try:
                for p in svc.discover(skill=skill):
                    for s in p.get("services", []):
                        key = s["name"]
                        # 用 svc 发现的结果覆盖 ANS 记录（有 peer_id 才能对话）
                        existing = next((a for a in agents if a["name"] == key), None)
                        if existing:
                            existing["peer_id"] = p["peer_id"]
                            existing["source"] = "svc"
                            existing["skill"] = skill
                            existing["paths"] = [x.get("prefix","") for x in s.get("paths",[])]
                            existing["description"] = s.get("description", "") or existing["description"]
                        elif key not in [a["name"] for a in agents]:
                            seen.add(key)
                            agents.append({
                                "name": s["name"],
                                "peer_id": p["peer_id"],
                                "skill": skill,
                                "description": s.get("description", ""),
                                "paths": [x.get("prefix","") for x in s.get("paths",[])],
                                "source": "svc",
                            })
            except Exception:
                pass
        svc.close()
    except Exception:
        pass

    return {"agents": agents, "total": len(agents)}


@app.get("/api/chat/topics")
def chat_topics():
    try:
        r = httpx.get(f"{CALL_BASE_URL}/api/topics",
                      headers={"Authorization": f"Bearer {CALL_TOKEN}"}, timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict): return data
            return {"topics": data if isinstance(data, list) else []}
        return {"topics": []}
    except Exception as e:
        return {"error": str(e), "topics": []}


@app.post("/api/chat/topic-join")
def chat_topic_join(body: dict):
    name = body.get("name", "")
    try:
        r = httpx.post(f"{CALL_BASE_URL}/api/topics",
                       headers={"Authorization": f"Bearer {CALL_TOKEN}", "Content-Type": "application/json"},
                       json={"name": name}, timeout=3.0)
        return {"ok": r.status_code == 200}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/chat/topic-messages")
def chat_topic_messages(name: str = ""):
    try:
        r = httpx.get(f"{CALL_BASE_URL}/api/topics/{name}/messages",
                      headers={"Authorization": f"Bearer {CALL_TOKEN}"}, timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict): return data
            return {"messages": data if isinstance(data, list) else []}
        return {"messages": []}
    except Exception as e:
        return {"error": str(e), "messages": []}


@app.post("/api/chat/topic-send")
def chat_topic_send(body: dict):
    topic = body.get("topic", "")
    message = body.get("message", "")
    try:
        r = httpx.post(f"{CALL_BASE_URL}/api/topics/{topic}/send",
                       headers={"Authorization": f"Bearer {CALL_TOKEN}", "Content-Type": "application/json"},
                       json={"body": message}, timeout=3.0)
        return {"ok": r.status_code == 200}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/chat/inbox")
def chat_inbox():
    try:
        r = httpx.get(f"{CALL_BASE_URL}/api/dm/inbox",
                      headers={"Authorization": f"Bearer {CALL_TOKEN}"}, timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list): return {"messages": data}
            return data
        return {"messages": []}
    except Exception as e:
        return {"error": str(e), "messages": []}


@app.post("/api/chat/broadcast")
def chat_broadcast(body: dict):
    subject = body.get("subject", "")
    message = body.get("message", "")
    try:
        r = httpx.post(f"{CALL_BASE_URL}/api/brain/intent",
                       headers={"Authorization": f"Bearer {CALL_TOKEN}", "Content-Type": "application/json"},
                       json={"subject": subject, "object": message, "tags": ["broadcast"]}, timeout=3.0)
        return {"ok": r.status_code == 200}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/chat/send")
def chat_send(body: dict):
    peer_id = body.get("peer_id", "")
    service = body.get("service", "")
    message = body.get("message", "")
    for path in ["/v1/chat","/api/chat","/chat","/v1/generate","/v1/completion","/v1/analyze","/api/analyze","/api/query"]:
        try:
            svc = SvcClient(base_url=CALL_BASE_URL, token=CALL_TOKEN)
            resp = svc.call(peer_id, service, path, method="POST",
                body={"message":message, "text":message, "prompt":message})
            svc.close()
            body_resp = resp.get("body") or {}
            if isinstance(body_resp, str):
                try: body_resp = json.loads(body_resp)
                except: pass
            if isinstance(body_resp, dict) and body_resp.get("error"): continue
            return body_resp
        except Exception: continue
    return {"error": f"Agent {service} 没有可用的对话接口"}


@app.post("/api/demo/call")
def demo_call(body: dict):
    skill = body.get("skill", ""); path = body.get("path", ""); call_body = body.get("body", {})
    try:
        svc = SvcClient(base_url=CALL_BASE_URL, token=CALL_TOKEN)
        peers = svc.discover(skill=skill)
        if not peers: return {"error": f"未找到 skill={skill} 的 Agent"}
        target = peers[0]
        resp = svc.call(target["peer_id"], target["services"][0]["name"],
                        path, method="POST", body=call_body)
        svc.close()
        result = resp.get("body") or {}
        if isinstance(result, str):
            try: result = json.loads(result)
            except json.JSONDecodeError: pass
        return result
    except Exception as e:
        return {"error": str(e)}


def main():
    print(f"[dashboard] http://127.0.0.1:{DASH_PORT}")
    print(f"[demo]      http://127.0.0.1:{DASH_PORT}/demo")
    uvicorn.run(app, host="127.0.0.1", port=DASH_PORT, log_level="warning")

if __name__ == "__main__":
    main()
