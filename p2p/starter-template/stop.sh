#!/usr/bin/env bash
# 停止所有 P2P 演示相关进程
set -euo pipefail
echo "→ 停止 Agent..."
pkill -f agent_a_supplier 2>/dev/null || true
pkill -f agent_b_compliance 2>/dev/null || true
pkill -f agent_c_logistics 2>/dev/null || true
pkill -f dashboard.py 2>/dev/null || true
echo "→ 停止 daemon..."
pkill -f "anet daemon" 2>/dev/null || true
lsof -ti tcp:13921,13922,13923,13924 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti tcp:7411,7412,7413,7500 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 2
echo "✓ 已停止所有进程"
