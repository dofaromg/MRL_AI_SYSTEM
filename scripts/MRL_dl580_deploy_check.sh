#!/usr/bin/env bash
# MRL_DL580 自運行部署檢查
# origin_signature=MrLiouWord
# DL580 為 MRL 內部母體自運行主節點；GitHub 為鏡像通道；Cloud Code 為建構器。
set -euo pipefail

MRL_PORT="${MRL_PORT:-8790}"
ORIGIN_SIGNATURE="MrLiouWord"

echo "MRL_DL580_DEPLOY_CHECK"
echo "origin_signature=${ORIGIN_SIGNATURE}"
echo "target_port=${MRL_PORT}"

# 1. Node 運轉環境
if ! command -v node >/dev/null 2>&1; then
  echo "FAIL: node runtime not found on DL580 node"
  exit 1
fi
echo "node=$(node --version)"

# 2. Runtime 主檔存在
if [ ! -f "MRL_RuntimeServer.js" ]; then
  echo "FAIL: MRL_RuntimeServer.js missing"
  exit 1
fi
echo "runtime_entry=MRL_RuntimeServer.js present"

# 3. Health 檢查（若 Runtime 已長駐）
if command -v curl >/dev/null 2>&1; then
  if curl -fsS "http://127.0.0.1:${MRL_PORT}/health" >/dev/null 2>&1; then
    echo "health=reachable"
  else
    echo "health=not running (start with: npm start)"
  fi
fi

echo "MRL_DL580_DEPLOY_CHECK_DONE"
