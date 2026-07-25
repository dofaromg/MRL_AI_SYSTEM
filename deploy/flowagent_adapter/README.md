# MRL_FlowAgent_SovereignAdapter_v1（重新包裝建構）

origin_signature: `MrLiouWord` ｜ 裁定：root 產品名取回、外部名降備註附錄（2026-07-25）

`flowagent` = FlowAgent 品牌啟動包裝器。你全程使用 FlowAgent 命名（指令 / `FLOWAGENT_*` 環境變數 / `FLOWAGENT.md`・`~/.flowagent.json` 設定檔 / `flowagent-*` 模型名），包裝器在內部把功能識別字轉譯給底層外部 CLI——外部名只存在於包裝器內部（附錄層），不對外、不升格。

對照表與原則：`docs/MRL_FlowAgent_Naming_Adapter_Map_v1.md`

```bash
install -m 755 flowagent ~/.local/bin/flowagent
FLOWAGENT_CODE_SAFE_MODE=1 flowagent --model flowagent-sonnet-5
```

當下狀態（沙盒 2026-07-25）：轉譯邏輯測試 PASS ×3（env 轉譯／不覆蓋既有功能變數／模型別名重寫／設定檔 symlink 以 FlowAgent 檔為本體）。接真實底層 CLI 實機驗收待起動。
