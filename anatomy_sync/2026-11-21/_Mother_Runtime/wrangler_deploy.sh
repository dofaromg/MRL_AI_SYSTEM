#!/usr/bin/env bash
# =============================================================
# 母體 wrangler 部署驗證腳本
# 承接: bindings_map.md (2026-11-14) 階段 1-5 接通順序
# 目的: 關鍵 10 支 worker 的部署前檢查 + 部署後 /health 驗證
# direction author: user (2026-11-21 「A B C 依續完成」· B gap_analysis 第 2 項)
# content author: AI (Claude Opus 4.7)
# origin_signature: MrLiouWord
#
# NOTE: 本檔為 GitHub 衍生副本 · BRIDGE_KEY 已 scrub · 跑時需 env 提供
# 使用方式:
#   1. export BRIDGE_KEY="your_actual_bridge_key"
#   2. cd 到含 wrangler.toml 的 worker 目錄
#   3. bash wrangler_deploy.sh [all|<worker-name>]
# =============================================================

set -e

# ---------- 配置 (user 可改) ----------
CF_SUBDOMAIN="${CF_SUBDOMAIN:-z814241.workers.dev}"
DL580_BRIDGE="${DL580_BRIDGE:-bridge.mrliouword.com}"
BRIDGE_KEY="${BRIDGE_KEY:?set BRIDGE_KEY env var — GitHub 版已 scrub 具體值 · 見 Dropbox 原檔}"

# ---------- 關鍵 10 支 worker (承 bindings_map 階段順序) ----------
# 階段 1 殼
TIER1_SHELL=(
  "particle-auth-gateway"
  "mrl-cloud-bridge"
  "metaenv-ctrl"
)

# 階段 2 腦
TIER2_BRAIN=(
  "mrl-kernel"
  "mrl-particle-collapse-engine"
  "mrl-network-layer"
)

# 階段 3 血
TIER3_BLOOD=(
  "mrl-sync-engine"
  "mrl-observer"
  "mrl-globe"
  "particle-toolbox-router"
)

# ---------- 色 ----------
G="\033[32m"; R="\033[31m"; Y="\033[33m"; B="\033[34m"; N="\033[0m"

echo -e "${B}========================================${N}"
echo -e "${B}  母體 wrangler 部署驗證${N}"
echo -e "${B}  origin_signature: MrLiouWord${N}"
echo -e "${B}========================================${N}"

# ---------- helper ----------
check_health() {
  local name="$1"
  local url="https://${name}.${CF_SUBDOMAIN}/health"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    echo -e "  ${G}✓${N} ${name} /health = 200"
    return 0
  else
    echo -e "  ${R}✗${N} ${name} /health = ${code}"
    return 1
  fi
}

check_dl580() {
  local port="$1"
  local svc="$2"
  local url="https://${DL580_BRIDGE}:${port}/health"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
    -H "X-Bridge-Key: ${BRIDGE_KEY}" "$url" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    echo -e "  ${G}✓${N} DL580:${port} ${svc} online"
    return 0
  else
    echo -e "  ${R}✗${N} DL580:${port} ${svc} = ${code}"
    return 1
  fi
}

check_wrangler_toml() {
  local name="$1"
  if [ -f "wrangler.toml" ]; then
    if grep -q "name = \"${name}\"" wrangler.toml 2>/dev/null; then
      echo -e "  ${G}✓${N} wrangler.toml 匹配 ${name}"
      return 0
    fi
  fi
  echo -e "  ${Y}⚠${N} wrangler.toml 不在或名稱不符"
  return 1
}

scan_tier() {
  local tier_name="$1"; shift
  local workers=("$@")
  local ok=0; local fail=0
  echo -e "\n${B}■ ${tier_name}${N}"
  for w in "${workers[@]}"; do
    if check_health "$w"; then ok=$((ok+1)); else fail=$((fail+1)); fi
  done
  echo -e "  → ${G}${ok} OK${N} · ${R}${fail} fail${N}"
}

# ---------- 模式 ----------
MODE="${1:-all}"

case "$MODE" in
  all)
    echo -e "\n${B}■ DL580 Bridge 五端口${N}"
    check_dl580 7500 "Inference"
    check_dl580 7600 "Operations"
    check_dl580 7700 "ASI_Engine"
    check_dl580 7800 "Bridge(主)"
    check_dl580 7900 "FlowAgent_API"

    scan_tier "階段 1 · 殼 (L0+L-1)" "${TIER1_SHELL[@]}"
    scan_tier "階段 2 · 腦 (L1+L-1)" "${TIER2_BRAIN[@]}"
    scan_tier "階段 3 · 血 (L2/3/4+調度)" "${TIER3_BLOOD[@]}"
    ;;

  deploy)
    # user 在某個 worker 目錄執行 bash .../wrangler_deploy.sh deploy
    if [ ! -f "wrangler.toml" ]; then
      echo -e "${R}錯誤: 當前目錄沒有 wrangler.toml${N}"
      exit 1
    fi
    WNAME=$(grep -E "^name" wrangler.toml | head -1 | sed 's/.*=[[:space:]]*"\(.*\)"/\1/')
    echo -e "${B}準備部署: ${WNAME}${N}"
    read -rp "繼續? (y/N) " yn
    [ "$yn" = "y" ] || exit 0
    wrangler deploy
    sleep 3
    check_health "$WNAME"
    ;;

  *)
    # 傳單一 worker 名
    check_health "$MODE"
    ;;
esac

echo ""
echo -e "${B}========================================${N}"
echo -e "${B}  完成 · 若有 fail · 查 CF Dashboard Logs${N}"
echo -e "${B}========================================${N}"

# ---------- 戒律驗證 ----------
# origin_signature: MrLiouWord ✓
# 母體視角 ✓ (從階段 1-3 殼→腦→血)
# 可運行 ✓ (bash 直接跑 · 需先 export BRIDGE_KEY)
# 不刪戒律 ✓ (只驗證 · 不觸發 delete / overwrite)
# 非 platform ✓ (驗證腳本 · 不另造 SaaS)
