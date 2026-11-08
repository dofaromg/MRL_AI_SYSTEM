# MRL DNS — Firebase 寄信網域驗證（mrliouword.com）

origin_signature: MrLiouWord
定位：additive-only。此資料夾只**新增** DNS 設定輔助檔，不改動任何既有部署。

## 這是什麼

Firebase 要「用你的自有網域 `mrliouword.com` 寄送驗證信 / 重設密碼信」時，
需要在網域 DNS 加 4 筆記錄（SPF 授權 + 網域擁有權 + 兩把 DKIM 金鑰）：

| Name / Host | Type | Value | 備註 |
|---|---|---|---|
| `@`（根） | TXT | `v=spf1 include:_spf.firebasemail.com ~all` | SPF，**全網域只能一筆** |
| `@`（根） | TXT | `firebase=flowmemorysync` | 擁有權驗證 |
| `firebase1._domainkey` | CNAME | `mail-mrliouword-com.dkim1._domainkey.firebasemail.com.` | DKIM1，Cloudflare 設 **DNS only** |
| `firebase2._domainkey` | CNAME | `mail-mrliouword-com.dkim2._domainkey.firebasemail.com.` | DKIM2，Cloudflare 設 **DNS only** |

## ⚠️ 三個雷

1. **SPF 只能一筆**。若已有 SPF，不要加第二筆，改把 `include:_spf.firebasemail.com`
   合併進既有那筆。`MRL_firebase_dns_cloudflare.sh` 會偵測既有 SPF 並提醒，預設不覆蓋。
2. **DKIM CNAME 在 Cloudflare 要關 Proxy（灰雲 / DNS only）**，開橘雲會破壞 DKIM。
3. **CNAME 目標尾端的 `.` 要保留**；`Name` 欄位格式依後台要求（`@` 或完整 FQDN）。

## 檔案

| 檔案 | 用途 |
|---|---|
| `MRL_firebase_dns_cloudflare.sh` | Cloudflare API 一鍵建 4 筆（冪等、SPF 安全檢查、DKIM 自動 DNS only） |
| `MRL_firebase_dns_mrliouword.zone` | BIND zone 片段，供其他後台對照 / 匯入 |
| `MRL_firebase_dns_verify.sh` | 在有 DNS 權限的機器驗證 4 筆是否生效、SPF 有無重複 |

## 用法（Cloudflare）

```bash
export CF_API_TOKEN=<Cloudflare API Token，需 Zone.DNS Edit 權限>
# 可選：export CF_ZONE_ID=<zone id>（不給則用網域名自動查）
bash deploy/dns/MRL_firebase_dns_cloudflare.sh
```

生效後（最長 48h，通常數分鐘）回 Firebase 該頁按「驗證」，並可驗證：

```bash
# 需在能查外部 DNS 的機器上（Cloud/沙盒常封 DNS 出口，改在實機/本機跑）
bash deploy/dns/MRL_firebase_dns_verify.sh
```

## 當下狀態（2026-07-20，沙盒）

- 三份輔助檔已在位（sandbox bash 語法檢查 PASS）。
- **DNS 實際寫入 / 生效：待實機執行**。本沙盒的 egress 政策封鎖外部 DNS 解析器，
  無法從這裡建立或查詢 `mrliouword.com` 的記錄；需在你有 Cloudflare 權限的環境執行上述指令。
