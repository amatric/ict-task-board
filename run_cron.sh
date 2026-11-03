#!/usr/bin/env bash
# 定时任务包装脚本：记录日志 + 失败重试 1 次
set -uo pipefail
cd "$(dirname "$0")" || exit 1
LOG_DIR=logs
mkdir -p "$LOG_DIR"
STAMP=$(date '+%Y%m%d-%H%M%S')

python3 fetch_trending.py --days 7 --top 30 >> "$LOG_DIR/cron-$STAMP.log" 2>&1
if [ $? -ne 0 ]; then
  echo "[WARN] 首次失败，10 秒后重试一次" >> "$LOG_DIR/cron-$STAMP.log"
  sleep 10
  python3 fetch_trending.py --days 7 --top 30 >> "$LOG_DIR/cron-$STAMP.log" 2>&1
fi
