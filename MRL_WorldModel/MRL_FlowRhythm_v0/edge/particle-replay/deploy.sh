#!/usr/bin/env bash
# 取回線上 particle-replay 當前原碼 → 加上 /rhythm/* 補位 → 部署。需 CLOUDFLARE_API_TOKEN、CLOUDFLARE_ACCOUNT_ID。
# 原碼只放在本目錄暫存（.gitignore），不入 repo。舊版本留在 Cloudflare 版本歷史，可隨時回滾。
set -euo pipefail
cd "$(dirname "$0")"
API="https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/particle-replay"
curl -sf -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" "$API/content/v2" -o .live.raw
python3 - <<'PY'
import email, re
raw = open(".live.raw", "rb").read()
b = raw.split(b"\r\n", 1)[0]
msg = email.message_from_bytes(b"Content-Type: multipart/form-data; boundary=" + b[2:] + b"\r\n\r\n" + raw)
parts = [p for p in msg.walk() if p.get_filename()]
js = [p for p in parts if p.get_filename().endswith(".js")][0].get_payload(decode=True).decode()
if "/rhythm" in js: raise SystemExit("線上已是補位版本，不重複包")
open("shell-deploy.js", "w").write(js)
PY
npx --yes wrangler@4 deploy
