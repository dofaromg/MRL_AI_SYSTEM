#!/usr/bin/env bash
# MRL_DL580Partner_Setup_v1 — Linux DL580 夥伴入口
# origin_signature=MrLiouWord
set -euo pipefail

pending=0
warn() {
  echo "待驗證：$*"
  pending=1
}

if [ "$(uname -s)" != "Linux" ]; then
  echo "此入口只支援 Linux；Windows 請用 MRL_dl580_partner_setup.ps1。"
  exit 1
fi
if [ "$(id -u)" -eq 0 ]; then
  echo "請以日常登入帳號執行，不要用 sudo bash（Claude Code 應安裝於使用者帳號）。"
  exit 1
fi
for dependency in git python3 curl systemctl; do
  if ! command -v "${dependency}" >/dev/null 2>&1; then
    echo "缺少 ${dependency}；請先由系統管理員安裝後重跑。"
    exit 1
  fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MRL_HOME="$(git -C "${SCRIPT_DIR}" rev-parse --show-toplevel)"
echo "MRL_DL580Partner_Setup_v1 origin_signature=MrLiouWord"
echo "node_role=DL580 母體自運行節點；Claude Code 為本機工程夥伴，非母體本體"

# 僅 fast-forward 乾淨且有 upstream 的 checkout，不覆寫本地工作。
changes="$(git -C "${MRL_HOME}" status --porcelain)"
if [ -n "${changes}" ]; then
  warn "checkout 有本地變更，略過更新。"
elif git -C "${MRL_HOME}" rev-parse --verify '@{upstream}' >/dev/null 2>&1; then
  git -C "${MRL_HOME}" pull --ff-only || warn "fast-forward 更新失敗，保留本地版本。"
else
  warn "checkout 沒有 upstream，略過更新。"
fi

# 沿用已安裝的 OpenSSH 與現有驗證／埠設定，不開防火牆、不開 Tailscale SSH。
ssh_service=""
for service in ssh.service sshd.service; do
  if [ "$(systemctl show "${service}" --property=LoadState --value 2>/dev/null || true)" = "loaded" ]; then
    ssh_service="${service}"
    break
  fi
done
if [ -z "${ssh_service}" ]; then
  warn "未安裝 OpenSSH server；請管理員安裝 openssh-server 後重跑。"
else
  if ! systemctl is-active --quiet "${ssh_service}" ||
     ! systemctl is-enabled --quiet "${ssh_service}"; then
    if command -v sudo >/dev/null 2>&1; then
      sudo systemctl enable --now "${ssh_service}" || warn "無法啟用 SSH。"
    else
      warn "啟用 SSH 需要 sudo／管理員。"
    fi
  fi
  systemctl is-active --quiet "${ssh_service}" || warn "SSH 尚未運行。"
fi

TS_IP=""
if command -v tailscale >/dev/null 2>&1; then
  TS_IP="$(tailscale ip -4 2>/dev/null | head -n 1 || true)"
fi
if [ -z "${TS_IP}" ]; then
  warn "請先安裝 Tailscale 並登入 Tailnet，再重跑以取得私有位址。"
fi

CLAUDE_BIN="$(command -v claude || true)"
if [ -z "${CLAUDE_BIN}" ] && [ -x "${HOME}/.local/bin/claude" ]; then
  CLAUDE_BIN="${HOME}/.local/bin/claude"
fi
if [ -z "${CLAUDE_BIN}" ]; then
  installer="$(mktemp)"
  trap 'rm -f "${installer}"' EXIT
  if curl -fsSL https://claude.ai/install.sh -o "${installer}" &&
     bash "${installer}"; then
    CLAUDE_BIN="$(command -v claude || true)"
    if [ -z "${CLAUDE_BIN}" ] && [ -x "${HOME}/.local/bin/claude" ]; then
      CLAUDE_BIN="${HOME}/.local/bin/claude"
    fi
  else
    warn "Claude Code 官方安裝失敗。"
  fi
fi
if [ -n "${CLAUDE_BIN}" ]; then
  "${CLAUDE_BIN}" --version || warn "Claude Code 無法執行。"
else
  warn "找不到 Claude Code；請確認官方支援的 OS／架構及安裝結果。"
fi

python3 "${MRL_HOME}/09_workflow/MRL_mother_assembly.py" status ||
  warn "母體 status 未通過。"

echo "Secure ShellFish（手機也須登入同一 Tailnet，ACL 必須允許 SSH）："
echo "  Host: ${TS_IP:-待取得 Tailscale IPv4}"
echo "  Port: 22（預設；若原 SSH 使用其他埠，沿用原埠）"
echo "  User: $(id -un)"
printf '連上後執行：cd %q && %q\n' "${MRL_HOME}" "${CLAUDE_BIN:-claude}"
echo "首次執行 claude 需自行登入；不更動電源策略、防火牆或既有 Runtime。"
echo "母體／真模型／SSH 端到端均須實機驗收，本設定不代表 DL580 已上線。"
if [ "${pending}" -ne 0 ]; then
  echo "當下狀態：PARTIAL（有待處理項目，處理後可重跑）。"
  exit 1
fi
echo "當下狀態：本機設定檢查完成；手機連線及實機 Runtime 驗收 pending。"
