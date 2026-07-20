#!/usr/bin/env bash
# MRL_firebase_dns_verify.sh
# origin_signature=MrLiouWord
#
# 用途：在「有對外 DNS 查詢權限」的機器上（例如 DL580 / 你本機 / WSL / git-bash）
#       驗證 mrliouword.com 的 Firebase 寄信 4 筆記錄是否已生效，並檢查 SPF 沒有重複。
#
# 注意：此腳本需要能查外部 DNS。Cloud/沙盒環境常封鎖 DNS 出口，屬正常，請改在實機跑。
#
# 用法：
#   bash deploy/dns/MRL_firebase_dns_verify.sh
#   MRL_DNS_DOMAIN=mrliouword.com bash deploy/dns/MRL_firebase_dns_verify.sh
set -uo pipefail

DOMAIN="${MRL_DNS_DOMAIN:-mrliouword.com}"
FAIL=0
pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1"; FAIL=1; }
warn() { echo "WARN: $1"; }

echo "MRL_FIREBASE_DNS_VERIFY"
echo "origin_signature=MrLiouWord"
echo "domain=${DOMAIN}"

# 選一個可用的查詢器：dig 優先，否則 nslookup（Windows git-bash 也有）
QTOOL=""
if command -v dig >/dev/null 2>&1; then QTOOL="dig"
elif command -v nslookup >/dev/null 2>&1; then QTOOL="nslookup"
else
  echo "FAIL: 找不到 dig 或 nslookup，無法查 DNS。請在有 DNS 工具的機器上執行。"
  exit 2
fi
echo "resolver_tool=${QTOOL}"

# 回傳指定 name/type 的所有記錄值（一行一筆）
lookup() { # $1=name $2=type
  if [ "${QTOOL}" = "dig" ]; then
    dig +short "$2" "$1" 2>/dev/null
  else
    # nslookup 輸出較雜，抽出等號右側 / canonical name
    nslookup -type="$2" "$1" 2>/dev/null \
      | grep -iE 'text =|canonical name =' \
      | sed -E 's/.*(text|canonical name) = //I'
  fi
}

# ── 1) SPF ─────────────────────────────────────────────────────────
TXT_ROOT="$(lookup "${DOMAIN}" TXT)"
SPF_LINES="$(printf '%s\n' "${TXT_ROOT}" | grep -i 'v=spf1' || true)"
SPF_COUNT="$(printf '%s\n' "${SPF_LINES}" | grep -c 'v=spf1' || true)"

if [ "${SPF_COUNT}" -gt 1 ]; then
  fail "SPF 有 ${SPF_COUNT} 筆（只能 1 筆）— 請合併。目前：${SPF_LINES}"
elif [ "${SPF_COUNT}" -eq 1 ]; then
  if printf '%s' "${SPF_LINES}" | grep -qi '_spf.firebasemail.com'; then
    pass "SPF 單筆且含 _spf.firebasemail.com"
  else
    fail "SPF 存在但未包含 include:_spf.firebasemail.com — 需合併。目前：${SPF_LINES}"
  fi
else
  fail "根網域查不到 SPF（v=spf1）記錄"
fi

# ── 2) 擁有權 TXT ──────────────────────────────────────────────────
if printf '%s' "${TXT_ROOT}" | grep -qi 'firebase=flowmemorysync'; then
  pass "擁有權 TXT firebase=flowmemorysync 存在"
else
  fail "查不到 TXT firebase=flowmemorysync"
fi

# ── 3) DKIM CNAMEs（比對「完整」目標主機，避免前綴被竄改/打錯仍誤判 PASS）──
# Firebase 目標格式為 mail-<網域,點換成減號>.dkimN._domainkey.firebasemail.com
DOMAIN_DASH="$(printf '%s' "${DOMAIN}" | tr '.' '-')"
EXP_D1="mail-${DOMAIN_DASH}.dkim1._domainkey.firebasemail.com"
EXP_D2="mail-${DOMAIN_DASH}.dkim2._domainkey.firebasemail.com"
# 正規化：去頭尾空白、去結尾點、轉小寫，再做完整字串比對
norm_host() { printf '%s' "$1" | tr 'A-Z' 'a-z' | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/\.$//'; }
D1="$(norm_host "$(lookup "firebase1._domainkey.${DOMAIN}" CNAME)")"
D2="$(norm_host "$(lookup "firebase2._domainkey.${DOMAIN}" CNAME)")"
if [ "${D1}" = "${EXP_D1}" ]; then
  pass "DKIM1 CNAME 完整指向 ${EXP_D1}"
else
  fail "firebase1._domainkey 應指向 ${EXP_D1}，實得：${D1:-空}"
fi
if [ "${D2}" = "${EXP_D2}" ]; then
  pass "DKIM2 CNAME 完整指向 ${EXP_D2}"
else
  fail "firebase2._domainkey 應指向 ${EXP_D2}，實得：${D2:-空}"
fi

echo "----------------------------------------"
if [ "${FAIL}" -eq 0 ]; then
  echo "MRL_FIREBASE_DNS_VERIFY_PASS（4 筆皆生效；回 Firebase 按驗證即可）"
  exit 0
else
  echo "MRL_FIREBASE_DNS_VERIFY_PENDING（尚未全綠；DNS 可能還在生效，最長 48h，稍後重跑）"
  exit 1
fi
