#!/usr/bin/env bash
# MRL_firebase_dns_cloudflare.sh
# origin_signature=MrLiouWord
#
# 用途：在 Cloudflare 為 mrliouword.com 建立 Firebase「用自有網域寄信」所需的 4 筆 DNS 記錄。
#   1) TXT  @  v=spf1 include:_spf.firebasemail.com ~all      (SPF 授權寄信)
#   2) TXT  @  firebase=flowmemorysync                        (網域擁有權驗證)
#   3) CNAME firebase1._domainkey  -> mail-mrliouword-com.dkim1._domainkey.firebasemail.com  (DKIM1, DNS only)
#   4) CNAME firebase2._domainkey  -> mail-mrliouword-com.dkim2._domainkey.firebasemail.com  (DKIM2, DNS only)
#
# 安全設計：
#   - Token 只從環境變數讀取，不寫死在檔案。
#   - 冪等：已存在的記錄會 SKIP，不重複建立。
#   - SPF 只能有一筆：若偵測到既有 SPF，一律「不」自動加第二筆（多筆 SPF 會全部失效），
#     改印出正確的合併建議（include 會插在終端 all 之前）。原本沒有 SPF 時才自動建立。
#   - DKIM CNAME 一律 proxied=false（DNS only / 灰雲），開 Proxy 會破壞 DKIM。
#
# 前置：
#   export CF_API_TOKEN=<Cloudflare API Token，需 Zone.DNS Edit 權限>
#   （可選）export CF_ZONE_ID=<zone id>   # 不給則用網域名自動查
#   （可選）export MRL_DNS_DOMAIN=mrliouword.com
#   需要 curl 與 jq。
#
# 執行：
#   bash deploy/dns/MRL_firebase_dns_cloudflare.sh
set -uo pipefail

DOMAIN="${MRL_DNS_DOMAIN:-mrliouword.com}"
API="https://api.cloudflare.com/client/v4"

: "${CF_API_TOKEN:?請先 export CF_API_TOKEN=<你的 Cloudflare API Token（需 Zone.DNS Edit 權限）>}"
CF_ZONE_ID="${CF_ZONE_ID:-}"

command -v curl >/dev/null 2>&1 || { echo "FAIL: 需要 curl"; exit 1; }
command -v jq   >/dev/null 2>&1 || { echo "FAIL: 需要 jq（Debian/Ubuntu: apt-get install jq）"; exit 1; }

AUTH=(-H "Authorization: Bearer ${CF_API_TOKEN}" -H "Content-Type: application/json")

echo "MRL_FIREBASE_DNS_CLOUDFLARE"
echo "origin_signature=MrLiouWord"
echo "domain=${DOMAIN}"

# 1) 取得 Zone ID
if [ -z "${CF_ZONE_ID}" ]; then
  CF_ZONE_ID=$(curl -sS "${AUTH[@]}" "${API}/zones?name=${DOMAIN}" | jq -r '.result[0].id // empty')
fi
if [ -z "${CF_ZONE_ID}" ]; then
  echo "FAIL: 找不到 zone ${DOMAIN}。請確認 Token 權限，或手動 export CF_ZONE_ID。"
  exit 1
fi
echo "zone_id=${CF_ZONE_ID}"

# helper：某 type+name 底下，content 是否已含指定子字串（大小寫不敏感）
record_exists() { # $1=type $2=fqdn $3=content_substr
  curl -sS "${AUTH[@]}" "${API}/zones/${CF_ZONE_ID}/dns_records?type=${1}&name=${2}" \
    | jq -e --arg c "$3" '.result[] | select((.content|ascii_downcase) | contains($c|ascii_downcase))' \
      >/dev/null 2>&1
}

FAIL_COUNT=0

create() { # $1=type $2=fqdn $3=content $4=proxied(true/false) $5=match_substr
  local type="$1" name="$2" content="$3" proxied="$4" match="$5"
  if record_exists "${type}" "${name}" "${match}"; then
    echo "SKIP  已存在: ${type} ${name}"
    return 0
  fi
  local body resp
  body=$(jq -nc --arg t "${type}" --arg n "${name}" --arg c "${content}" --argjson p "${proxied}" \
    '{type:$t, name:$n, content:$c, ttl:1, proxied:$p}')
  resp=$(curl -sS "${AUTH[@]}" -X POST "${API}/zones/${CF_ZONE_ID}/dns_records" --data "${body}")
  if echo "${resp}" | jq -e '.success==true' >/dev/null 2>&1; then
    echo "OK    建立: ${type} ${name}"
  else
    echo "FAIL  建立: ${type} ${name} -> $(echo "${resp}" | jq -c '.errors' 2>/dev/null)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    return 1
  fi
}

# 2) SPF 安全檢查（SPF 只能一筆）
EXISTING_SPF=$(curl -sS "${AUTH[@]}" "${API}/zones/${CF_ZONE_ID}/dns_records?type=TXT&name=${DOMAIN}" \
  | jq -r '.result[] | select((.content|ascii_downcase)|test("v=spf1")) | .content' 2>/dev/null)

SKIP_SPF=0
if [ -n "${EXISTING_SPF}" ]; then
  echo "⚠️  偵測到既有 SPF：${EXISTING_SPF}"
  # 已存在 SPF 時「一律」不自動新增第二筆——多筆 SPF 會讓全部 SPF 失效，
  # 沒有任何覆寫可以安全繞過（原先的 MRL_FORCE_SPF 反而會製造第二筆，已移除）。
  SKIP_SPF=1
  if echo "${EXISTING_SPF}" | grep -qi "_spf.firebasemail.com"; then
    echo "    已含 _spf.firebasemail.com，SPF 無需變更。"
  else
    # 把 include 插在「終端 all 機制」之前，並保留原本的修飾（~all / -all / ?all / +all）。
    # 直接接在 -all 之後會讓 include 永遠不被評估（all 一律 match），等於沒授權 Firebase。
    MERGED_SPF=$(printf '%s' "${EXISTING_SPF}" \
      | sed -E 's/[[:space:]]*([-~?+]?all)[[:space:]]*$/ include:_spf.firebasemail.com \1/')
    if [ "${MERGED_SPF}" = "${EXISTING_SPF}" ]; then
      MERGED_SPF="${EXISTING_SPF} include:_spf.firebasemail.com"   # 原本沒有終端 all
    fi
    echo "    SPF 只能一筆，不自動新增。請手動把既有 SPF『合併』為（include 需在終端 all 之前）："
    echo "    ${MERGED_SPF}"
  fi
fi

if [ "${SKIP_SPF}" != "1" ]; then
  create TXT "${DOMAIN}" "v=spf1 include:_spf.firebasemail.com ~all" false "v=spf1 include:_spf.firebasemail.com"
fi

# 3) 網域擁有權 TXT
create TXT "${DOMAIN}" "firebase=flowmemorysync" false "firebase=flowmemorysync"

# 4) DKIM CNAME（DNS only）
create CNAME "firebase1._domainkey.${DOMAIN}" "mail-mrliouword-com.dkim1._domainkey.firebasemail.com" false "dkim1._domainkey.firebasemail.com"
create CNAME "firebase2._domainkey.${DOMAIN}" "mail-mrliouword-com.dkim2._domainkey.firebasemail.com" false "dkim2._domainkey.firebasemail.com"

if [ "${FAIL_COUNT}" -gt 0 ]; then
  echo "FAIL  共 ${FAIL_COUNT} 筆記錄建立失敗，請確認 Token 權限後重跑。"
  exit 1
fi
echo "DONE。等生效（最長 48h，通常數分鐘）後，回 Firebase 該頁按「驗證」。"
echo "驗證生效狀態：bash deploy/dns/MRL_firebase_dns_verify.sh"
