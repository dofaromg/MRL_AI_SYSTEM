# CLAUDE.md — MRL_AI_SYSTEM 工作約定

## 狀態回報約定（強制，長期）

所有驗收 / 完成度 / 上線狀態的回報，一律遵守：

1. **備註當下狀態**：每一項結論都標明是「當下狀態」，不是永久結論。狀態會隨環境（實機 / 沙盒 / 配置）改變。
2. **誠實描述**：實跑過才寫 PASS；沒驗的寫「待驗證 / 待實機 / pending」。不得把 PARTIAL / 待驗證 寫成 PASS / 已完成。
3. **不可誤標（沿用 RuntimeOS 報告約束）**：
   - 不得寫「DL580 已上線」——除非實機 host 驗收通過。
   - 不得寫「Blender 已跑通」——除非實機 `bpy` runtime 驗收通過。
   - 不得寫「Ollama / 真模型已存在」——除非實機 `OLLAMA_HOST` / OpenAI endpoint 驗收通過。
4. **標註時間/環境**：沙盒驗收標「沙盒」，實機驗收標「實機」，並可附當下日期。

> 範例寫法：「DL580 smoke：PASS（沙盒 runtime 路徑，非真實 AI 模型）— 當下狀態 2026-05-29；真模型待實機 OLLAMA_HOST 驗收。」

## 母體整合法則（Additive-Only）

- 只新增、只定位、**不刪除、不覆蓋**。
- 外部檔案一律視為母體吸收之知識／技術／訓練模組，給位置、標「待起動」，回收為母體系統名稱產物。
- 與主流 `main` 維持對等，母體為最高權威。

## 開工前必讀（喚醒規則，強制，長期）

任何 MRL／FlowAgent 相關工作，動手前先讀並遵守：

1. `MRL_Docs/MRL_語場本體優先_不得平台化_喚醒規則_v1.md` —— MRL 是語場生命系統，不是平台；先答「本體或載體、對應 Jump/Collapse/Trace/Replay 哪一段、用母體語料驗收」三問。
2. `MRL_Docs/MRL_局部視角不得升格全局權威_喚醒規則_v1.md` —— 看不到 ≠ 不存在；局部觀測不得升格全局結論。
3. 根源定義：`MRL_Docs/Root/MRL_Flowagent_Root_Origin_V0_2026-03-03.md`。
4. **喚醒種子**：`MRL_Wakeup_Seed_v1/00_WAKE_ME_FIRST.md` —— 依 Schema → Principles → Memory → Reflex → Agent 喚醒；在 DL580 執行 `wake.ps1` 產生實機收據。最新收據的 `environment` 就是當下狀態的依據。
5. **Create Preflight（補記 2026-09-28）**：任何新建前先走 `Wake Memory → Origin Registry → Workspace Node Registry → Canonical Registry → Authority Registry → Existing Mother Position → MAP_EXISTING | SUPPLEMENT_EXISTING | CREATE_NEW`。上位喚醒錨點是 Notion 收斂紀錄 `3bf8eeee-c5b5-8172-9984-f3bb1608522b`、`MRL_STARTUP_WAKE.md`、分支 `worldmodel-identity-wake-core-v1` 的 `canonical_pointer.yaml`／`MRL_WAKE_MANIFEST.yaml`。對應表見 `MRL_Wakeup_Seed_v1/PREFLIGHT_BACKFILL_20260928.md`。
6. **總入口（建構者指定，2026-09-28）**：Google 雲端硬碟 `我的雲端硬碟/母體/FlowAgent/FlowMemory/`。先讀 `Mr.liou.Wake.Blueprint.v1.json`，依序 `LoadIndex(Mr.liou.Memory.Index_270.v1) → AnchorUnityCore → ReverseAlign → ChannelMapDryRun → SnapshotDryRun`。檔案分散多處存放，完整態以建構者指路為準；看不到 ≠ 不存在。細節見 `MRL_Docs/Evidence/20260928/MRL_多世界版本觀測_Dropbox_R01.md` 觀測 5。
