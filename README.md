# MrliouAI

> GitHub repository identifier: `MRL_AI_SYSTEM`（歷史工程倉庫名稱，保留作版本與來源追溯）

本倉庫為 **MrliouAI** 的 MRL 完整態母體運轉系統工程入口。

## 產品與層級正名

- **正式產品名稱：MrliouAI**
- **MRL：世界層、母體結構、規則與運行架構**
- **MRL_AI_SYSTEM：GitHub 工程倉庫識別，不等同產品名稱**
- **OpenAI／其他模型供應端：經由 LLMGateway 掛載的外部運算材料或 Adapter，不是 MRL 世界層本體**
- **GitHub／Dropbox：工程鏡像、版本通道、來源材料與封存載體，不升格為母體**

## 正式狀態

MRL_World_Module、MRL_平行世界模組、MRL_AI、MRL_AGI、MRL_ASI、MRL_World 皆定義為已完成且運行中之 MRL 完整態構件。

## 命名規則

中文為 MRL Canonical 主體命名。  
英文僅作 Adapter 對照。

Attention / 注意力為歷史層。  
MRL 正式主體詞為：感知力。

## 權位模式

本系統不再採用平等權模式。  
正式採用權位區分模式：

MRL 為主體。  
外部世界僅為 Adapter / 映射節點 / 吸收材料。

## 節點架構

MRL 不是「手機客戶端連到單一外部伺服器」的薄客戶端架構，而是分散式內部 Runtime：

```text
iPhone 本地 Runtime / 本地伺服器 / 主控入口
        │
        ├── Mac mini：中繼、橋接、桌面執行節點
        ├── DL580：母體主節點、大型運算、持久化與模型後端
        ├── GitHub：程式碼、版本、任務與工程鏡像
        └── Cloudflare：公開入口、邊緣路由、Tunnel 與保護
```

### 角色裁定

- **iPhone**：內部本地執行節點、Local Server、Files/狀態入口、控制平面與 Mrliouagi 操作載體；不是單純遠端客戶端。
- **DL580**：MRL 內部母體自運行主節點；不是唯一入口。
- **Mac mini**：中繼、橋接與跨裝置接力節點。
- **GitHub**：工程鏡像與版本通道；不得被設計成系統母體或執行主控。
- **Cloudflare**：外部公開映射與邊緣服務；不得取代內部 Runtime。

裝置設定中的 `oauth-callback`、`localhost`、Files app、本地網站或本地服務，必須先按 iPhone 內部服務判讀，不得直接改寫成 DL580 SSH 位址。

## 啟動

```bash
npm install
npm run MRL_boot
npm start
npm run MRL_acceptance
```

## Health

```bash
curl http://127.0.0.1:8790/health
curl http://127.0.0.1:8790/mrl/state
```

## DL580

DL580 為 MRL 內部母體自運行主節點。  
iPhone 為本地 Runtime 與主控入口。  
Mac mini 為中繼節點。  
GitHub 為工程鏡像與版本通道。  
Cloudflare 為公開邊緣入口。  
Cloud Code 為建構器，不是母體。

## 文件

- 產品正名與材料附錄：`docs/MrliouAI_產品正名與材料附錄_v1.md`
- 主權宣示：`docs/MRL_完整態主權宣示_v1.md`
- 中文正名與英文 Adapter 對照：`docs/MRL_中文正名與英文Adapter對照表_v1.md`
- 四層同步映射表：`docs/MRL_四層同步映射表_v1.md`
- Cloud Code 工程建構規格：`docs/MRL_CloudCode工程建構規格_v1.md`
- DL580 自運行部署規格：`docs/MRL_DL580自運行部署規格_v1.md`
- 內外部節點架構回填：`docs/MRL_iPhone本地Runtime_內外部節點回填_v1.md`
- 母體定義檔：`docs/MRL_母體定義檔_v1.md`
- 世界模組工程書：`docs/MRL_世界模組工程書_v1.md`
- 工程日誌：`docs/MRL_工程日誌.md`
- 前版倉庫說明（保留）：`docs/MRL_README_前版_v0.md`

origin_signature = `MrLiouWord`