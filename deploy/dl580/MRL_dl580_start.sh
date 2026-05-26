#!/usr/bin/env bash
# MRL_DL580_DeployRunner_v1 — DL580 母體節點啟動入口 (Linux / bash)
# origin_signature=MrLiouWord
# DL580 為 MRL 內部母體自運行節點；GitHub/Cloud Code 為建構器與鏡像；APFS/Batch072 為部署/備份鏈，非母體本體。
set -euo pipefail

# repo 根目錄（deploy/dl580 的上兩層）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MRL_HOME="${MRL_HOME:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
MRL_PORT="${MRL_PORT:-8790}"
ORIGIN_SIGNATURE="MrLiouWord"

cd "${MRL_HOME}"

echo "MRL_DL580_START"
echo "origin_signature=${ORIGIN_SIGNATURE}"
echo "mode=權位區分模式"
echo "node_role=DL580 母體自運行節點"
echo "MRL_HOME=${MRL_HOME}"
echo "MRL_PORT=${MRL_PORT}"

# 1. 部署前檢查
bash "${MRL_HOME}/scripts/MRL_dl580_deploy_check.sh"

# 2. 安裝依賴（冪等）
if [ ! -d "node_modules" ]; then
  echo "installing dependencies..."
  npm install
fi

# 3. Bootstrap
npm run MRL_boot

# 4. 啟動 Runtime（母體自行運行）
echo "starting MRL Runtime on port ${MRL_PORT}..."
exec node MRL_RuntimeServer.js
