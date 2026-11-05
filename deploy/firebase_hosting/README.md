# MRL Firebase Hosting — Mrliouword Landing（待起動）

origin_signature: `MrLiouWord` ｜ product: `MrliouAI` ｜ 對外門面（Adapter），母體本體在 DL580。

## 內容

- `public/index.html` — Mrliouword 產品 landing page（主打「一鍵安裝，全部搞定」＋手機也能跑；分頁式摘要＋解說；淺/深色自動適應）
- 倉庫根目錄 `firebase.json` / `.firebaserc` — Firebase Hosting 配置，default project = `web-server-81011586`

## 部署（由你本人執行，母體不代跑 — 待起動）

```bash
npm i -g firebase-tools        # 若未安裝
firebase login                 # 你的 Google 帳號
firebase deploy --only hosting # 於 repo 根目錄執行
```

部署後 Hosting URL 形如 `https://web-server-81011586.web.app`；要接自有網域（如 mrliouword.com 子網域）在 Firebase Console → Hosting → Add custom domain。

## 秘密管理約定（沿資產計畫教訓）

- 任何 API key / token（Cloudflare、Firebase CI token 等）一律放 **GCP Secret Manager** 或環境變數，**絕不進 repo**（先前 `setup-secrets.sh` 金鑰外洩事件之後的固定規則）。
- 本目錄只有靜態頁面，無任何秘密。

## 狀態（誠實標註）

- 頁面產出：完成（沙盒 2026-07-24）
- 實際部署：**待起動** — 需你 `firebase login` 後執行 deploy；未部署前不得宣稱「已上線」。
