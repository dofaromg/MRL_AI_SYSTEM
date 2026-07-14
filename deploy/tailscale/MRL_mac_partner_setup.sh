#!/usr/bin/env bash
# MRL_MacPartner_Setup_v1 — 一鍵把 mac-mini 準備成「夥伴節點」(Claude Code on Mac)
# origin_signature=MrLiouWord
# 用途：把手動 SSH / 安裝 / clone 那一堆步驟壓成單一指令，讓夥伴(Claude Code)跑在 Mac 本機。
#       僅新增、不覆蓋既有設定 (Additive-Only)。冪等，可重複執行。
set -euo pipefail

ORIGIN_SIGNATURE="MrLiouWord"
REPO_URL="https://github.com/dofaromg/mrl_ai_system"
REPO_DIR_NAME="mrl_ai_system"
TS_FULL_DOMAIN="mac-mini-1.tail7de813.ts.net"

echo "==================================================="
echo " MRL_MacPartner_Setup_v1"
echo " origin_signature=${ORIGIN_SIGNATURE}"
echo " node_role=夥伴節點 (Claude Code on Mac)"
echo "==================================================="

# 0) 只在 macOS 上跑
if [ "$(uname -s)" != "Darwin" ]; then
  echo "❌ 這支腳本只在 macOS 上執行（偵測到 $(uname -s)）。"
  exit 1
fi

# 1) 顯示登入帳號 + Tailscale 位址（手機連線要用）
MAC_USER="$(whoami)"
echo
echo "▶ 登入帳號 (Shellfish 的 User 欄填這個)：${MAC_USER}"
TS_BIN="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
TS_IP=""
if [ -x "${TS_BIN}" ]; then
  TS_IP="$(${TS_BIN} ip -4 2>/dev/null | head -1 || true)"
  [ -n "${TS_IP}" ] && echo "▶ Tailscale IP：${TS_IP}"
fi

# 2) 開啟遠端登入 (SSH)；已開就略過
echo
if sudo systemsetup -getremotelogin 2>/dev/null | grep -qi "On"; then
  echo "✅ 遠端登入 (SSH) 已開啟"
else
  echo "▶ 開啟遠端登入 (需要輸入 Mac 密碼)…"
  sudo systemsetup -setremotelogin on
  echo "✅ 遠端登入 (SSH) 已開啟"
fi

# 3) 接電源時不自動睡眠，避免遠端連線中斷
echo "▶ 設定：接電源時不自動睡眠 (sudo pmset -c sleep 0)…"
sudo pmset -c sleep 0 || true

# 4) 安裝 Claude Code（沒裝才裝）
echo
if command -v claude >/dev/null 2>&1; then
  echo "✅ 已有 Claude Code：$(claude --version 2>/dev/null || echo installed)"
else
  echo "▶ 安裝 Claude Code…"
  curl -fsSL https://claude.ai/install.sh | bash
  echo "⚠ 安裝後請關掉終端機再重開，讓 PATH 生效。"
fi

# 5) 取得母體 repo（沒有就 clone，有就 fast-forward 更新）
echo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if git -C "${SCRIPT_DIR}" rev-parse --show-toplevel >/dev/null 2>&1; then
  MRL_HOME="$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)"
  echo "▶ 於既有 repo 更新：${MRL_HOME}"
  git -C "${MRL_HOME}" pull --ff-only || echo "⚠ pull 略過（可能有本地變更）"
else
  MRL_HOME="${HOME}/${REPO_DIR_NAME}"
  if [ -d "${MRL_HOME}/.git" ]; then
    echo "▶ 更新既有 clone：${MRL_HOME}"
    git -C "${MRL_HOME}" pull --ff-only || echo "⚠ pull 略過"
  else
    echo "▶ Clone 母體到 ${MRL_HOME}…"
    git clone "${REPO_URL}" "${MRL_HOME}"
  fi
fi

# 6) 沙盒層級 smoke：確認母體核心可跑（純 Python 標準庫，免安裝依賴）
echo
echo "▶ 母體核心 smoke (status)…"
if command -v python3 >/dev/null 2>&1; then
  python3 "${MRL_HOME}/09_workflow/MRL_mother_assembly.py" status \
    || echo "⚠ status 未通過，之後可再查（不影響連線設定）"
else
  echo "⚠ 找不到 python3，母體 Python 端需要它（macOS 內建通常已有）。"
fi

# 7) 收尾：印出手機連線資訊
echo
echo "==================================================="
echo " ✅ 完成。接下來（iPhone / Secure ShellFish）："
echo "   1) 新增連線："
echo "        Host: ${TS_FULL_DOMAIN}"
[ -n "${TS_IP}" ] && echo "              (或 IP: ${TS_IP})"
echo "        Port: 22"
echo "        User: ${MAC_USER}"
echo "   2) 連上後執行： cd ${MRL_HOME} && claude"
echo
echo "   夥伴(Claude Code)就跑在這台 Mac 上了。"
echo "==================================================="
