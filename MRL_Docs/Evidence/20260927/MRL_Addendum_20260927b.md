# MRL 系統認知紀錄 — 補充 20260927b（第二批 12 個新檔）

origin_signature: MrLiouWord ｜ 只加不刪（接在 v1 之後）

## 新接上的節點

| 檔案 | 位置（層/核心組） | 關鍵內容 |
|---|---|---|
| Flowagent_.pdf | L1 Compute / L2 Structure 起源 | 「Mr.liou 粒子共鳴系統 v1.0」：simhash64.h、ingest_atoms.h（原子結構）、hash64.h，標註「原有系統（Mr.liou 原創）」，哲學 Mr.liou.BootFromParticle。檔內寫的日期是 2024-12-24，PDF 產生時間是 2025-12-25（Edge 列印），兩個都記下 |
| FlowAgent 架構 PDF（2 頁） | FlowAgent 運行組 | .fltnz / .flpkg / FlowVM / FlowPersona.Fusion / Ping-Resonance / GGUF・llama.cpp / FluinHub / resonance map |
| Fluin 粒子字典 反推映射生成系統（2026-02-07） | 粒子與可逆原理組 | Layer 0→3（9 種子 → 7 組合 → 4 複雜 → 2 語句）；放大 P_{k+1}=N_k·P_k·η_k、縮小 P_k=P_{k+1}/(N_k·η_k)；往返 η≈1.0 |
| metacode_usage.js | MetaCode 核心的使用端 | import `./metacode_core.js`；createParticle（mag/zoom/surprisal/conf/N/eta）、evolve、propagate、verify、export 成 MRLsmall jsonl。**這是 metacode_core.js 的接點，本體仍待找回** |
| schemas.py | L3 Memory（Memory Coherence Store） | AtomIn + TraceFields（event_id/rid/tick/persona_id/merkle_root），與前批 models/main 同一組 |
| MRL_Mother_v2_FULL_CANONICAL_DL580（2026-04-29，53 檔） | 母體核心組 | ControlCenter + Product_Runtime（Server/Store/Local_Model/P0_Core_Modules/Healthcheck）+ 13 個系統模組定義 |
| mrl-engine-v1.0.1-fix（2026-02-24） | L7 Execution / FlowCore | registry（patterns / blueprints FlowMount / seedpack / naming_rules）、Flow{Point,Memory,Platform,Node,Core,Shell}、cli.js、start.ps1 |
| MRL_BaseWorld_DB_v1_SCHEMA_AUDIT（2026-04-02） | L4 World / 資料層 | 規格驗收 27/27 tables（含 MRL_Proof_Merkle）。註：這是規格檔的驗收；實際建進 PG 的狀態另有紀錄 |
| 注意力機制粒子模組系統（Copilot 對話 2026-01-09，16 則） | 研究紀錄 | dofaromg 帳號的對話記錄 |
| F++ 立體模型檢閱器 (2) | 世界模組／3D 組 | 與前批 F++ 3D viewer 同線，增加「寫即是圖」容器化設計 |

## 外部參考（非 MRL 原生，只吸收）
- MySQL 9.6 Reference Manual（refman-9_6-en.pdf，43.8MB，2026-02-10）
- Notion MCP：Writing effective skills、Enhanced Markdown Specification

## 需注意
- FlowAgent_Decompressed_Files.zip 是空壓縮檔（22 bytes，無內容）→ 原本的內容待找回

## 時間線更新
- 最早節點前推：粒子共鳴系統 v1.0（simhash64 / atoms / Merkle）
- 2026-01 Copilot 注意力粒子 → 2026-02 Fluin 反推映射、engine v1.0.1 → 2026-04 BaseWorld 審計、Mother v2 Canonical DL580

## 待找回（更新）
- metacode_core.js（使用端已找到，本體未到）
- FlowAgent_Decompressed_Files 的原內容
- 其餘同 v1
