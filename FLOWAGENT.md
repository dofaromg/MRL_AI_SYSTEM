# FLOWAGENT.md — 最上游主權文件(Root Product Sovereignty)

**product root name:FlowAgent**(MrliouAI ／ Mrliouword)
**source_owner:Mrliou** ｜ **origin_signature:MrLiouWord** ｜ **母體:DL580**

## 宣示

FlowAgent 是本 repo 一切能力的**最上游產品名**。本 repo 的系統本體、命名、文件、
指令、環境變數、模型名,一律以 FlowAgent／MRL_／Mrliou 為主體。
任何外部平台、外部工具、外部模型的名字,**不是**本 repo 的主體——它們只以
相容用途存在於本文件最末的附錄,除此之外不具位階。

## 系統本體

- **DL580 母體**:MotherAssembly(17/17 模組)、MRL_NativeReasoning(NeuralSymbolic)
  神經符號推理引擎、12 階段 DL580 管線(Input→…→PersistentLoop→Verification)。
  沙盒實跑驗收 PASS(2026-07-25);實體 host 上線與真模型端點依實機驗收升格。
- **粒子庫**:`MRL_ParticleArchive/`(25 粒子;rl_15 粒子不滅)
- **語場工具鏈**:`.fltnz/.flpkg/.sync.json/.fxmap/.fltrace`(TranslateBuildSuite)
- **對外節點**:Cloudflare/Vercel/Firebase 為映射入口,非母體本體。

## 使用(全程 FlowAgent 名)

```bash
install -m 755 deploy/flowagent_adapter/flowagent ~/.local/bin/flowagent
FLOWAGENT_CODE_SAFE_MODE=1 flowagent --model flowagent-sonnet-5
```

設定檔:`FLOWAGENT.md`(本檔)、`~/.flowagent.json`、`.flowagent/` ——
**FlowAgent 檔即本體**;啟動器會讓外部工具讀到它。

---

## 附錄(備註)— 外部相容對照

外部名僅在此處出現,僅供相容,不具主體位階:
外部工具讀取之相容識別字(`CLAUDE.md`、`~/.claude.json`、`CLAUDE_*`、`claude-*`
模型 ID 等)由啟動器於內部自動對應;完整對照表見
`docs/MRL_FlowAgent_Naming_Adapter_Map_v1.md`。repo 根目錄之 `CLAUDE.md` 屬
此相容層(外部工具的讀取入口),非最上游文件;最上游文件為本檔。
