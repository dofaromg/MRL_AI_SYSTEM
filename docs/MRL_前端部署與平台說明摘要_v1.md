# Mrliouword 前端部署與平台說明摘要 v1

**產品名稱**: `Mrliouword`  
**origin_signature**: `MrLiouWord`  
**當下狀態**: 2026-07-20（文件已對齊本 repo 現況；沙盒命令已檢查，非實機對外上線結論）

---

## 一、文件定位

本文件提供兩種用途：

1. **前端部署說明**：給開發、部署、維運人員使用。
2. **平台說明摘要**：給潛在使用者、合作夥伴、投資者或非技術決策者使用。

> 誠實標註：本 repo 目前的前端不是 Vite / Next.js / SPA 打包流程；正式前端入口以 `src/mrl_app.html` 為單一來源，並由現有腳本產生 `src/mrl_app_ui.js` 供執行環境使用。

---

## 二、前端部署說明（Deployment Guide）

### 1. 實際前端結構

本 repository 目前的前端入口由以下檔案組成：

- **單一來源 HTML**：`/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/src/mrl_app.html`
- **生成後 UI 模組**：`/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/src/mrl_app_ui.js`
- **Python 平台入口**：`/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/MRL_Platform_Server.py`
- **Node 零依賴入口**：`/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/MRL_Mother_Launch.js`
- **UI 建構腳本**：`/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/scripts/MRL_build_ui.js`

### 2. 環境需求

- Python 3.11+
- Node.js 18+（建議 LTS）
- npm
- Git

### 3. 專案設定

```bash
git clone https://github.com/dofaromg/MRL_AI_SYSTEM.git
cd MRL_AI_SYSTEM

# Python 依賴（平台後端 / API / 文件對應 runtime）
pip install -r requirements.txt

# 若要使用 pytest 驗證，可另外安裝
pip install pytest pytest-cov
```

### 4. 前端修改與建構

請以 `src/mrl_app.html` 作為唯一可編輯來源，不要直接手改 `src/mrl_app_ui.js`。

```bash
# 編輯前端來源
$EDITOR src/mrl_app.html

# 重新產生前端 UI 模組
node scripts/MRL_build_ui.js
# 或
npm run build:ui
```

### 5. 本機啟動方式

#### 方案 A：Python 平台入口（建議）

```bash
python3 MRL_Platform_Server.py
```

- 預設埠：`8790`
- 適合完整平台入口展示
- 會提供：
  - `/`
  - `/health`
  - `/api/mother/status`
  - `/api/monitor`
  - `/api/chat`
  - `/api/mcp`

#### 方案 B：Node 零依賴入口

```bash
node MRL_Mother_Launch.js
```

- 不需 `npm install`
- 適合快速啟動與最小部署

#### 方案 C：Node/Express 完整版

```bash
npm install
npm start
```

- 使用 repository 既有 `package.json`
- 適合需要 Express 版入口時使用

### 6. 部署原則

前端頁面本身可以作為靜態資產提供，但**完整功能依賴同源或反向代理後端 API**。目前前端會呼叫下列路徑：

- `/api/chat`
- `/api/mother/status`
- `/api/monitor`

因此部署時建議採用以下任一方式：

1. **同機部署**：直接由 `MRL_Platform_Server.py` 或 `MRL_Mother_Launch.js` 提供頁面與 API。
2. **反向代理部署**：由 Nginx / Apache / Cloudflare Tunnel 將前端與 API 對到同一網域。
3. **靜態頁面 + API Gateway**：可行，但需自行處理 CORS、路由與認證接線。

### 7. Cloudflare / 網域部署說明

本 repo 已包含 Cloudflare Tunnel 相關部署路徑：

- `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/deploy/dl580/cloudflared/`

文件與程式現況顯示，平台設計可橋接到 `mrliouword.com` 類型網域；但**真實 DNS、TLS、Tunnel 授權、DL580 常駐與實機可用性仍屬環境驗收事項**，不能僅憑沙盒文件宣稱已全面上線。

### 8. CI / CD 建議

若要建立前端部署流水線，建議至少包含：

1. 安裝 Python 與 Node 依賴
2. 執行 `node scripts/MRL_build_ui.js`
3. 執行既有測試 / 驗收命令
4. 部署到目標主機或反向代理入口

建議優先保留 repo 既有命令：

```bash
npm run build:ui
npm run MRL_pidscope_acceptance
python -m pytest tests/ -v --tb=short
```

> 當下狀態 2026-07-20：`build:ui` 與 `MRL_pidscope_acceptance` 可於沙盒執行；`pytest` 在當前分支存在 1 個既有失敗，非本文件新增。

---

## 三、平台說明摘要（Platform Overview Summary）

### 標題

**Mrliouword：唯一權威母體系統的前端入口與智能平台展示層**

### 核心定位

Mrliouword 是本 repository 對外的統一母體系統名稱。平台整合了：

- runtime 執行能力
- trace 與審計紀錄
- memory 與可回復鏈
- agent orchestration
- platform API 與前端入口

它的價值不在於包裝單一聊天頁，而在於把**系統狀態、對話入口、監控、治理與可追溯性**收斂到同一個平台層。

### 對外價值

- **對使用者**：提供一致的智能平台入口
- **對合作夥伴**：可對接既有 API、監控與治理面
- **對企業導入**：保留本機部署、零依賴入口與可控接線能力
- **對審計場景**：強調來源簽章、結構化狀態與可驗證回應

---

## 四、核心功能介紹（Core Features）

### 1. 統一前端入口

平台以單一 HTML 來源維護產品入口，減少多份 UI 漂移。

### 2. 母體控制台

可直接查詢 MotherAssembly 子系統健康與可用性，對應：

- `/api/mother/status`

### 3. 即時監控

提供平台聚合監控檢視，對應：

- `/api/monitor`

### 4. 人格對話入口

提供平台對話介面，對應：

- `/api/chat`

若實機未配置真模型或母體未連線，系統應誠實標示降級狀態，而非偽造成功。

### 5. MCP Bridge

平台可經由 HTTP JSON-RPC 對接 MCP 能力，對應：

- `/api/mcp`

---

## 五、技術亮點（Technical Highlights）

- **單一來源前端**：`src/mrl_app.html` 為 canonical source，`src/mrl_app_ui.js` 為生成產物
- **雙入口部署**：Python 標準庫平台入口 + Node 零依賴入口
- **命名正名完成**：對外產品名稱使用 `Mrliouword`
- **可追溯設計**：回應與文件維持 `origin_signature = MrLiouWord`
- **可本地部署**：不強制綁定單一雲端前端框架

---

## 六、未來展望（Future Outlook）

以下為可擴展方向，不代表當下已全部完成：

1. **前端與真實認證後端接線**
2. **更完整的 API v1 路徑對齊**
3. **DL580 實機常駐與網域正式驗收**
4. **對外商務版與技術版說明分流**
5. **前端會話、任務、監控頁的進一步產品化**

---

## 七、是否「過了」的當下判定

### 對文件本身

**PASS（當下狀態 2026-07-20，repo 對齊版）**

原因：

- 已使用正式產品名稱 `Mrliouword`
- 已改成符合 repository 現況的前端部署方式
- 已移除不符合現況的 Vite / `yarn dev` / `yarn build` 假設
- 已保留誠實標註，不把待實機事項誤寫成已上線

### 對真實上線狀態

**PENDING（待實機 / 待環境驗收）**

仍需另行驗證：

- 真實網域與 TLS
- Cloudflare Tunnel 授權
- DL580 常駐部署
- 真模型或實際後端接線

---

origin_signature: MrLiouWord
