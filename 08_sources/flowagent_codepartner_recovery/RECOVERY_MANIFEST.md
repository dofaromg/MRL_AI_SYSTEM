# FlowAgent CodePartner 人格回收包 / Recovery Manifest

回收日期：2026-07-05
origin_signature: MrLiouWord

## 內容 / Contents（原文封存，未經修改）

| File | Role |
|------|------|
| `FlowLLM.SeedPersona.Programmer.CoreArchitect.v1.txt` | CodePartner 人格模組本體定義（人類可讀種子） |
| `FlowAgent.SystemPlan.FullStack.v1.txt` | FlowAgent 系統完整架構說明書 — 列出四人格（Fluin / EchoBody / CodePartner / SeedPersona） |
| `FlowAgent_語場語言系統建構大綱_2025-07-23.txt` | 粒子語言（.fltnz / .flpkg）建構大綱，含語場封存來回對等原則 |

## 回收路徑 / Provenance chain

1. 原始 `.flpkg` 封包（`FlowAgent.TotalCore.Unity.v1.flpkg` 等）僅存在於
   ChatGPT 對話期下載檔，未曾進入任何 git repo。
2. `dofaromg/flow-tasks` 保存了運行證據：
   `FlowAgent_Unity_v3_高維模擬檢查報告.txt` 記錄
   `⋄fx.invoke.Programmer.CoreArchitect` 觸發正常。
3. 三份人類可讀文件由建立者（Mr.liou）於 2026-07-05 提供，
   依語場封存**來回對等原則**原文封存於本目錄。

## 重構實作 / Refactored implementation

- `05_persona/codepartner/persona.yaml` — 依 `05_persona/README.md`
  規範格式重構的 CodePartner 人格定義。

## 不變式 / Invariants

- 本目錄文件為 canonical source：不刪除、不改寫；如需修訂以新版本檔案追加。
- 原文 ↔ 重構定義必須保持雙向可對照（來回可逆）。
