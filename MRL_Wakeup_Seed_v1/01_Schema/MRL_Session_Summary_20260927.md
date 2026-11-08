# MRL 視窗總整理 — 2026-09-27

origin_signature: MrLiouWord ｜ 只加不刪

## 一、這個視窗完成的事
1. **LLVM 吸收方向定案**：MRL Dialect 建在 MLIR 上（pcode → Dialect → PVM / LLVM IR → x86 DL580 / Wasm CF Workers / ARM iPhone）。名稱釐清：MLIR 是外部框架，MRL 自有的是 MRLDialect。
2. **工作法定案**：你定義全圖，Claude 不審前提、只查接點；狀態只分「已對上原始檔／待找回」。
3. **拼圖**：三批上傳共 116 個獨立檔，全部定位到主線與 L(-1)–L7。
4. **親手實測**：
   - fltnz_parser 對 270 筆記憶做來回轉換，結果逐位元組相同
   - PVM 可以跑，但跳躍指令有缺陷
   - Backwrite 20260609 的校驗碼 6/6 正確
   - Batch03A gate 418/418
5. **證據鏈**：
   - 系統認知紀錄 v1.1 + 116 檔 SHA-256 清單
   - 放在 GitHub `dofaromg/MRL_AI_SYSTEM`，分支 `evidence/mrl-cognition-20260927`
   - Google Drive 和 Dropbox 各有 `MRL_Evidence_20260927` 資料夾
   - Claude 記憶 `mrl-system-cognition`
   - Claude Doc 和 Notion LLVM-MRL-v1 頁
6. **時間線**：
   - 起點：粒子共鳴系統 v1.0（simhash64 / atoms / Merkle，檔內日期 2024-12-24）
   - 2025-07：FlowAgent.Runtime v1–v49
   - 2025-12：MRLIOU_zero
   - 2026-02：Fluin 反推映射、engine v1.0.1
   - 2026-03：parser / PVM
   - 2026-04：Mother v2 Canonical DL580
   - 2026-07：部署
   - 2026-09：WorldModel LLM

## 二、DL580 D:\ 截圖所見（2026-03-21 整批落地）
- **引擎線**：
  - mrl-engine v1.0 / v1.0.1-fix / v12 / v12-final / v13
  - mrl-dl580-engine v1.0 / v1.1 / v1.2
  - MRL_Engine_v12_FlowExec、MRL_FlowExec v1.0 / v1.1
- **粒子線**：
  - mrl_asi_particle_engine（v1 / v2）、mrl_asi_server
  - particle-system-hub-v2.1、particle-toolbox-router-v1.1、particle-mcp-server、particle-team-mcp
  - mcp-particle-ai、mrl-globe-v3.1
- **核心／治理**：
  - MrlCore、mrlcore_registry、mrliou-closure-kernel v1.0.1、mrliou_closed_loop_container
  - MrLiouWord-Protection-Package、MRL_Naming_Law_v2、MRL_OfficialMemory_Export_v1
  - Patent_Application_Draft、MRL_PhaseR_Assessment、MRL_Session_20260317_PhaseRUN
- **產品**：
  - MRL_CareOS（Standard v1 / v2.0 / FINAL / UPDATE）
  - MRL_Product_Engineering_Package v1 / v2
  - mrlsillyai-complete-v1、hansillyai-mrl-patch-v2
- **大檔**：
  - 平行時空.zip（約 2.0GB）
  - flowagent_final 3.zip（99MB）
  - 反推映射放大鏡系統 技術實現方案.md
- **對照**：D:\ 上有 mrl-engine-v1.0.1-fix.zip，大小 19767 bytes，與本視窗收到並已雜湊的同名檔大小一致

## 三、安全待辦（重要）
- 截圖中出現**明文 Cloudflare API token**（Invoke-WebRequest 的 Bearer 標頭）→ 需要撤銷並重發
- meta_world_portal.js 寫死了 Upstash token → 需要更換，改成讀環境變數
- auto-login.html 會直接簽出 local-admin 的 JWT cookie；如果它放在公開的 workers.dev 網域，等於任何人都能登入 → 請確認只在本機
- CareOS 全員密碼被重設成同一組 → 正式給機構使用前，每個人要改成各自的密碼
- 本紀錄**不收錄**任何 token 或人員姓名

## 四、待找回
- seed_origin.py、metacode_core.js（使用端已找到）、TotalCore.Unity.v1.js、seed_index.json
- MetaEnv.*.pcode、FunctionMatrix.pcode 的解碼方式
- FlowAgent_Decompressed_Files 的原內容（收到的是空 zip）
- LLVM-MRL 的實際執行輸出
- OneDrive：Microsoft 365 連接器尚未完成登入
