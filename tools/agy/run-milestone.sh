#!/usr/bin/env bash
# Giao một milestone cho Argon (agy) và giữ tiến trình sống tới khi xong.
# agy --print thoát ngay khi Argon kết thúc lượt chờ subagent -> subagent bị hủy.
# Vì vậy dùng --input-format stream-json và giữ stdin mở cho tới khi log có dấu "MILESTONE_XONG".
# Cách dùng: bash tools/agy/run-milestone.sh M2   (đọc prompt từ tools/agy/prompt-M2.txt)
set -u
cd "$(dirname "$0")/../.."
M="$1"
PROMPT_FILE="tools/agy/prompt-$M.txt"
LOG="tools/agy/logs/run-$M.ndjson"
GIOI_HAN_GIAY="${2:-7200}"
shift 2 2>/dev/null || shift $#
CO_THEM=("$@")   # cờ bổ sung cho agy, ví dụ --dangerously-skip-permissions (người dùng đã đồng ý)
mkdir -p tools/agy/logs
: > "$LOG"

noi_dung=$(python -c "import json,sys; print(json.dumps({'event':'user','message':{'content':open(sys.argv[1],encoding='utf-8').read()}}))" "$PROMPT_FILE")

{
  printf '%s\n' "$noi_dung"
  bat_dau=$(date +%s)
  # giữ stdin mở; agy tự đánh thức Argon khi subagent xong
  # chỉ tính dấu xong trong sự kiện result (prompt chuyển cho subagent cũng chứa chuỗi này)
  until grep '"event":"result"' "$LOG" 2>/dev/null | grep -q "MILESTONE_XONG"; do
    if [ $(( $(date +%s) - bat_dau )) -gt "$GIOI_HAN_GIAY" ]; then echo "QUA_GIO" >&2; break; fi
    sleep 15
  done
} | agy --input-format=stream-json --output-format=stream-json --model=gemini-4-argon-medium "${CO_THEM[@]}" --print="" >> "$LOG" 2>&1
echo "{\"event\":\"runner_exit\",\"code\":$?}" >> "$LOG"
