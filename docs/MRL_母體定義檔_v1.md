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
| Adapter | `MRL_Adapters/` | GitHub、CloudCode、OpenAI、Cloudflare、Docker、DL580 |
| 部署 | `deploy/` | dl580、tailscale、docker、systemd |

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
  "attention_policy": "Attention/注意力為歷史層；MRL正式主體為感知力"
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

- **DL580**：母體自運行主節點。
- **GitHub**：工程鏡像與版本通道。
- **Cloud Code**：建構器。

三者皆非母體本體；母體本體為 MRL 完整態運轉系統本身。

---

## 五、Runtime 候選（待驗證收斂紀錄；尚未升格主體）

審計：`docs/MRL_Runtime_Canonical_Report_v1.md`（分支 `MRL_Branch_Runtime_Convergence_Audit_v1`）。

目前存在多套 runtime 候選（A Python IR 核心 #37 / B PIDScope ownership / C DL580 Engine 7700 /
D JS v1.2.0 core / E Mother Product Runtime / F 3D / G FlowCore 家族 / I RuntimeServer / H d1_schema）。

- 全部以 reference + sha256 登錄，**未刪除、未 bulk-copy**（LAW-2 additive）。
- **尚未**選定任一為「主體 Runtime」；待 MrLiou 裁示後才升格回填本檔。
- 命名違規候選標 `待正名`，非刪除理由。

> 本節僅為待驗證收斂紀錄，不構成主體升格。
