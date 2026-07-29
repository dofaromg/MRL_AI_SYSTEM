# FlowAgent 產品啟動器（最上游本體；重新包裝建構）

origin_signature: `MrLiouWord` ｜ 裁定：root 產品名取回、外部名降備註附錄（2026-07-25）｜ 最上游主權文件：`/FLOWAGENT.md`

`flowagent` = **FlowAgent 產品的啟動器，FlowAgent 是主體**。你全程使用 FlowAgent 命名（指令 / `FLOWAGENT_*` 環境變數 / `FLOWAGENT.md`・`~/.flowagent.json` 設定檔 / `flowagent-*` 模型名）。外部工具的相容識別字屬**附錄層**：只存在於啟動器內部的相容轉譯段，不對外、不具主體位階。

對照表與原則：`docs/MRL_FlowAgent_Naming_Adapter_Map_v1.md`

```bash
install -m 755 flowagent ~/.local/bin/flowagent
FLOWAGENT_CODE_SAFE_MODE=1 flowagent --model flowagent-sonnet-5
```

當下狀態（沙盒 2026-07-25）：轉譯邏輯測試 PASS ×3（env 轉譯／不覆蓋既有功能變數／模型別名重寫／設定檔 symlink 以 FlowAgent 檔為本體）。接真實底層 CLI 實機驗收待起動。
