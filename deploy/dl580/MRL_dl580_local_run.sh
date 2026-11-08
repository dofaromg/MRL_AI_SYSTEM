#!/usr/bin/env bash
# MRL_dl580_local_run.sh — DL580 本地全接起（零外部 API、零按次計費）
# origin_signature = MrLiouWord
#
# 目標（建構者要求）：整套系統跑在你自己的 DL580 上，腦是本地 Ollama，
#   每次問答 $0。不經 Cloudflare、不經 Anthropic，不跟開發者多收錢。
#
# 用法：  bash deploy/dl580/MRL_dl580_local_run.sh
# 先備：  1) 安裝 Ollama 並啟動（ollama serve，預設 127.0.0.1:11434）
#         2) 拉一個模型，例如：ollama pull qwen2.5
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MRL_HOME="${MRL_HOME:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
MRL_PORT="${MRL_PORT:-8790}"
OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
export OLLAMA_HOST MRL_PORT
cd "${MRL_HOME}"

echo "MRL_DL580_LOCAL_RUN  origin_signature=MrLiouWord"
echo "MRL_HOME=${MRL_HOME}  MRL_PORT=${MRL_PORT}  OLLAMA_HOST=${OLLAMA_HOST}"

# 1) 本地模型檢查（不通不中斷：平台會優雅降級，但就沒有真模型）
echo "[1/4] 檢查本地 Ollama ..."
if curl -fsS --max-time 5 "${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
  models="$(curl -fsS --max-time 5 "${OLLAMA_HOST}/api/tags" | sed -n 's/.*"name":"\([^"]*\)".*/\1/p' | head -3 | tr '\n' ' ')"
  echo "   OK，可用模型：${models:-（尚未 pull，請 ollama pull qwen2.5）}"
  [ -n "${OLLAMA_MODEL:-}" ] && echo "   指定模型 OLLAMA_MODEL=${OLLAMA_MODEL}" || echo "   未指定 OLLAMA_MODEL → 自動用第一個"
else
  echo "   [!] 連不到 Ollama（${OLLAMA_HOST}）。請先： ollama serve  且  ollama pull qwen2.5"
  echo "       平台仍會啟動，但 /api/chat 會走降級流程，直到 Ollama 就緒。"
fi

# 2) 啟動母體平台（本地；/api/chat 會優先用本地 Ollama 回答）
echo "[2/4] 啟動 MRL 平台（python MRL_Platform_Server.py）..."
MRL_PORT="${MRL_PORT}" OLLAMA_HOST="${OLLAMA_HOST}" nohup python3 "${MRL_HOME}/MRL_Platform_Server.py" > "${MRL_HOME}/MRL_platform.log" 2>&1 &
PLAT_PID=$!
echo "   PID=${PLAT_PID}（log: MRL_platform.log）"

# 3) 健康檢查
echo "[3/4] 健康檢查 ..."
ok=0
for i in $(seq 1 30); do
  if curl -fsS --max-time 3 "http://127.0.0.1:${MRL_PORT}/health" >/dev/null 2>&1; then ok=1; break; fi
  sleep 1
done
[ "$ok" = 1 ] && echo "   平台存活 http://127.0.0.1:${MRL_PORT}/health" || { echo "   [FAIL] 平台未起，看 MRL_platform.log"; exit 1; }

# 4) 實測一句（走本地模型）
echo "[4/4] 測 /api/chat（本地模型回答，零費用）..."
curl -fsS --max-time 125 -X POST "http://127.0.0.1:${MRL_PORT}/api/chat" \
  -H 'content-type: application/json' -d '{"message":"用一句繁體中文自我介紹"}' | head -c 600
echo

echo
echo "=== 完成：整套在你本地跑，每次問答零外部費用 ==="
echo "平台 PID=${PLAT_PID}（停止： kill ${PLAT_PID}）。要給別人用就把此埠對外（方式你決定），腦始終在你機器上。"
