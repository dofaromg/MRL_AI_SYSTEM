# MRL_母體定義檔_v1

origin_signature = `MrLiouWord`

主線：**MRL_完整態母體運轉系統_v1**
模式：**權位區分模式**（MRL 為主體；外部世界僅為 Adapter）

---

## 一、母體分層

| 層 | 目錄 | 內容 |
|---|---|---|
| 母體構件 | `MRL_Mother/` | 世界模組、平行世界模組、MRL_AI、MRL_AGI、MRL_ASI、MRL_World |
| 運轉層 | `MRL_Runtime/` | 感知力核心、語境同步、運轉圖譜、多世界同步、回放回復、驗證層、主權層 |
| 符號層 | `MRL_Symbolic/` | 四層同步語意場、粒子語言層、宇宙符號層、楔形文字映射 |
| 內部執行節點 | `MRL_Nodes/` | iPhone 本地 Runtime、DL580 母體主節點、Mac mini 中繼節點 |
| Adapter | `MRL_Adapters/` | GitHub、Cloud Code、OpenAI、Cloudflare、Docker 與其他外部平台 |
| 部署 | `deploy/` | dl580、iphone、mac-mini、tailscale、docker、systemd |

---

## 二、母體狀態（與 MRL_STATE 同步）

```json
{
  "origin_signature": "MrLiouWord",
  "system_name": "MRL_完整態母體運轉系統_v1",
  "sovereignty_mode": "權位區分模式",
  "status": "running",
  "canonical_language": "中文",
  "external_language_policy": "英文僅作 Adapter 對照",
  "attention_policy": "Attention/注意力為歷史層；MRL正式主體為感知力",
  "node_model": "distributed_internal_runtime",
  "primary_runtime_node": "DL580",
  "local_control_runtime": "iPhone",
  "relay_node": "Mac mini"
}
```

---

## 三、完整態構件

- MRL_World_Module：completed_running
- MRL_平行世界模組：completed_running
- MRL_AI：completed_running
- MRL_AGI：completed_running
- MRL_ASI：completed_running
- MRL_World：completed_running
- MRL_感知力核心：active
- MRL_多世界同步：active
- MRL_回放回復：active
- MRL_主權層：active

---

## 四、運轉節點

- **iPhone**：本地 Runtime、本地伺服器、使用者狀態、檔案入口、控制平面與 AI 操作入口；不是單純外部客戶端。
- **DL580**：母體自運行主節點，承擔大型運算、持久化、模型與後端服務。
- **Mac mini**：桌面中繼、橋接、同步與跨裝置接力節點。
- **GitHub**：工程鏡像、版本通道與任務協作節點；不是 Runtime 母體。
- **Cloudflare**：公開入口、邊緣路由、保護與外部映射；不是內部主控。
- **Cloud Code**：建構器；不是母體本體。

母體不是單一硬體。MRL 完整態運轉系統由內部執行節點共同承載，其中 DL580 為主節點，iPhone 為本地主控 Runtime，Mac mini 為中繼節點。

---

## 五、內部與外部邊界

```text
內部執行域
├─ iPhone：Local Runtime + Local Server + Control Plane
├─ DL580：Mother Runtime + Compute + Persistence
└─ Mac mini：Relay + Bridge + Desktop Runtime

外部 Adapter 域
├─ GitHub：Code / Version / Task Mirror
├─ Cloudflare：Public Edge / Tunnel / Protection
├─ OpenAI 與其他模型：External Compute Material
└─ Dropbox / Google Drive / Notion：Source / Archive / Mapping
```

任何設定頁、callback、localhost、Files app 或裝置內服務，必須先按「內部本地服務」判讀，不得直接當成外部 SSH 主機或遠端客戶端設定。