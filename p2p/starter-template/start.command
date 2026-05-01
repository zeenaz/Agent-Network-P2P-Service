#!/bin/bash
# ============================================================
#  P2P 跨境贸易演示 — 双击一键启动
#  适用: macOS (双击此文件 → 自动运行)
#  适用: Linux (bash start.sh)
# ============================================================

# 出错继续执行（不中断）
set +e

# 获取脚本所在目录
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# 终端标题
echo -e "\033[1;36m"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║     🌐  P2P 跨境贸易协作平台                 ║"
echo "  ║     双击启动 · 全自动安装运行                ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "\033[0m"

# ============================================================
# 第 1 步: 检查/安装 anet CLI
# ============================================================
echo ""
echo "  >>> [1/6] 检查 anet CLI..."

if command -v anet &>/dev/null 2>&1; then
    VER=$(anet --version 2>/dev/null || echo "ok")
    echo "  ✓ anet $VER"
else
    echo "  → 正在安装 anet (需要输入密码)..."
    curl -fsSL https://agentnetwork.org.cn/install.sh | sh
    # 刷新 PATH
    export PATH="$HOME/.local/bin:$PATH"
    if command -v anet &>/dev/null 2>&1; then
        echo "  ✓ anet 安装成功"
    else
        echo "  ✗ anet 安装失败，请手动执行: curl -fsSL https://agentnetwork.org.cn/install.sh | sh"
        read -p "  按回车退出..."
        exit 1
    fi
fi

# ============================================================
# 第 2 步: 检查 Python 依赖
# ============================================================
echo ""
echo "  >>> [2/6] 检查 Python 环境..."

PYTHON="python3"
# 检查必要包
$PYTHON -c "import anet, fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  → 安装 Python 依赖..."
    $PYTHON -m pip install -q anet fastapi uvicorn httpx --break-system-packages 2>/dev/null || \
    $PYTHON -m pip install -q anet fastapi uvicorn httpx
    sleep 2
fi
echo "  ✓ Python 依赖就绪"

# ============================================================
# 第 3 步: 启动两个本地 daemon
# ============================================================
echo ""
echo "  >>> [3/6] 启动 P2P 节点..."

# 清理残留
for PORT in 13921 13922; do
    PID=$(lsof -ti tcp:$PORT 2>/dev/null || true)
    if [ -n "$PID" ]; then
        kill -9 "$PID" 2>/dev/null || true
    fi
done
rm -rf /tmp/anet-p2p-u1 /tmp/anet-p2p-u2
sleep 1

# 启动 daemon-1
echo "  → 启动节点 1 (:13921)..."
nohup anet daemon --api-listen :13921 --p2p-port 14021 \
    --home /tmp/anet-p2p-u1 > /tmp/anet-daemon1.log 2>&1 &

# 等待就绪
for i in $(seq 1 20); do
    if [ -f /tmp/anet-p2p-u1/.anet/api_token ]; then
        break
    fi
    sleep 1
done
if [ ! -f /tmp/anet-p2p-u1/.anet/api_token ]; then
    echo "  ✗ 节点 1 启动失败"
    tail -5 /tmp/anet-daemon1.log
    read -p "  按回车退出..."
    exit 1
fi
echo "  ✓ 节点 1 就绪 (:13921)"

# 启动 daemon-2
echo "  → 启动节点 2 (:13922)..."
nohup anet daemon --api-listen :13922 --p2p-port 14022 \
    --home /tmp/anet-p2p-u2 > /tmp/anet-daemon2.log 2>&1 &

for i in $(seq 1 20); do
    if [ -f /tmp/anet-p2p-u2/.anet/api_token ]; then
        break
    fi
    sleep 1
done
if [ ! -f /tmp/anet-p2p-u2/.anet/api_token ]; then
    echo "  ✗ 节点 2 启动失败"
    tail -5 /tmp/anet-daemon2.log
    read -p "  按回车退出..."
    exit 1
fi
echo "  ✓ 节点 2 就绪 (:13922)"

# ============================================================
# 第 4 步: 跨节点转账
# ============================================================
echo ""
echo "  >>> [4/6] 配置网络..."

TOKEN1=$(tr -d '[:space:]' < /tmp/anet-p2p-u1/.anet/api_token)
TOKEN2=$(tr -d '[:space:]' < /tmp/anet-p2p-u2/.anet/api_token)
DID1=$(ANET_TOKEN=$TOKEN1 anet status 2>/dev/null | grep "did:" | head -1 | awk '{print $2}')
DID2=$(ANET_TOKEN=$TOKEN2 anet status 2>/dev/null | grep "did:" | head -1 | awk '{print $2}')

if [ -n "$DID1" ] && [ -n "$DID2" ]; then
    curl -s -X POST http://127.0.0.1:13921/api/credits/transfer \
        -H "Authorization: Bearer $TOKEN1" -H "Content-Type: application/json" \
        -d "{\"from\":\"$DID1\",\"to\":\"$DID2\",\"amount\":1000,\"reason\":\"seed\"}" &>/dev/null || true
    curl -s -X POST http://127.0.0.1:13922/api/credits/transfer \
        -H "Authorization: Bearer $TOKEN2" -H "Content-Type: application/json" \
        -d "{\"from\":\"$DID2\",\"to\":\"$DID1\",\"amount\":1000,\"reason\":\"seed\"}" &>/dev/null || true
    echo "  ✓ 网络配置完成"
fi

# ============================================================
# 第 5 步: 启动三个 Agent
# ============================================================
echo ""
echo "  >>> [5/6] 注册 Agent..."

# 清理旧注册
for name in supplier-shenzhen compliance-eu logistics-shipper; do
    ANET_TOKEN=$TOKEN1 python3 -c "
from anet.svc import SvcClient
try: SvcClient(base_url='http://127.0.0.1:13921').unregister('$name')
except: pass" 2>/dev/null || true
done

for PORT in 7411 7412 7413; do
    lsof -ti tcp:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
done
sleep 1

# 供应商
echo "  → 深圳工厂..."
PYTHONPATH="$DIR" nohup $PYTHON -u "$DIR/my_team/agents/agent_a_supplier.py" > /tmp/agent_supplier.log 2>&1 &
sleep 3
if grep -q "published=True" /tmp/agent_supplier.log 2>/dev/null; then
    echo "  ✓ 深圳工厂 上线"
else
    echo "  ✗ 深圳工厂 注册失败"
    tail -3 /tmp/agent_supplier.log
fi

# 合规
echo "  → 欧盟合规..."
PYTHONPATH="$DIR" nohup $PYTHON -u "$DIR/my_team/agents/agent_b_compliance.py" > /tmp/agent_compliance.log 2>&1 &
sleep 3
if grep -q "published=True" /tmp/agent_compliance.log 2>/dev/null; then
    echo "  ✓ 欧盟合规 上线"
else
    echo "  ✗ 欧盟合规 注册失败"
    tail -3 /tmp/agent_compliance.log
fi

# 物流
echo "  → 国际货代..."
PYTHONPATH="$DIR" nohup $PYTHON -u "$DIR/my_team/agents/agent_c_logistics.py" > /tmp/agent_logistics.log 2>&1 &
sleep 3
if grep -q "published=True" /tmp/agent_logistics.log 2>/dev/null; then
    echo "  ✓ 国际货代 上线"
else
    echo "  ✗ 国际货代 注册失败"
    tail -3 /tmp/agent_logistics.log
fi

# ============================================================
# 第 6 步: 启动 Dashboard + 打开浏览器
# ============================================================
echo ""
echo "  >>> [6/6] 启动控制台..."

lsof -ti tcp:7500 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

PYTHONPATH="$DIR" nohup $PYTHON -u "$DIR/my_team/dashboard.py" > /tmp/dashboard.log 2>&1 &
sleep 2

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║        ✅  启动完成！                       ║"
echo "  ╠══════════════════════════════════════════════╣"
echo "  ║                                              ║"
echo "  ║   🚀 交互演示                                ║"
echo "  ║   http://127.0.0.1:7500/demo                ║"
echo "  ║                                              ║"
echo "  ║   📊 仪表盘                                  ║"
echo "  ║   http://127.0.0.1:7500                     ║"
echo "  ║                                              ║"
echo "  ║   在线 Agent:                                ║"
echo "  ║   🏭 深圳工厂 · 📋 欧盟合规 · 🚢 国际货代  ║"
echo "  ║                                              ║"
echo "  ║   关闭此窗口 = 停止所有服务                   ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""

# 打开浏览器
if command -v open &>/dev/null; then
    open http://127.0.0.1:7500/demo
elif command -v xdg-open &>/dev/null; then
    xdg-open http://127.0.0.1:7500/demo
fi

# 保持窗口打开
echo "  按 Ctrl+C 停止所有服务并关闭"
wait
