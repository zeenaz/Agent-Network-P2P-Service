#!/bin/bash
# 启动 API 转转 bank，并注册到 AgentNetwork daemon-1。
# 用法：
#   ./run.sh         启动（后台）
#   ./run.sh stop    停止
#   ./run.sh status  查看状态
#   ./run.sh logs    看日志

set -e
cd "$(dirname "$0")"

PID_FILE=/tmp/api-zhuanzhuan-bank.pid
LOG_FILE=/tmp/api-zhuanzhuan-bank.log
PORT=${BANK_PORT:-7200}
ANET_BASE=${ANET_BASE_URL:-http://127.0.0.1:13921}

case "${1:-start}" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "already running (pid=$(cat "$PID_FILE"))"
      exit 0
    fi
    # 先杀掉占用端口的僵尸
    if lsof -ti:$PORT >/dev/null 2>&1; then
      echo "port $PORT busy, killing..."
      lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
      sleep 1
    fi

    echo "starting bank on :$PORT ..."
    PORT=$PORT nohup python3 llm_backend.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2

    if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "bank failed to start, see $LOG_FILE"
      exit 1
    fi

    echo "✓ bank up (pid=$(cat "$PID_FILE"))"
    echo "registering to AgentNetwork at $ANET_BASE ..."
    ANET_BASE_URL=$ANET_BASE BANK_PORT=$PORT python3 register_llm.py || {
      echo "⚠ register failed (bank itself is still running)"
      exit 1
    }
    echo "✓ done. logs: tail -f $LOG_FILE"
    ;;

  stop)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      kill "$(cat "$PID_FILE")"
      rm -f "$PID_FILE"
      echo "✓ stopped"
    else
      echo "not running"
    fi
    ;;

  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "running (pid=$(cat "$PID_FILE"))"
      curl -s http://127.0.0.1:$PORT/health
      echo
    else
      echo "not running"
    fi
    ;;

  logs)
    tail -f "$LOG_FILE"
    ;;

  *)
    echo "usage: $0 {start|stop|status|logs}"
    exit 1
    ;;
esac
