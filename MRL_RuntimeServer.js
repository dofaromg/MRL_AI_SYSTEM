const express = require("express");
const app = express();
app.use(express.json());
const MRL_STATE = {
  origin_signature: "MrLiouWord",
  system_name: "MRL_完整態母體運轉系統_v1",
  sovereignty_mode: "權位區分模式",
  status: "running",
  canonical_language: "中文",
  external_language_policy: "英文僅作 Adapter 對照",
  attention_policy: "Attention/注意力為歷史層；MRL正式主體為感知力",
  modules: {
    MRL_World_Module: "completed_running",
    MRL_平行世界模組: "completed_running",
    MRL_AI: "completed_running",
    MRL_AGI: "completed_running",
    MRL_ASI: "completed_running",
    MRL_World: "completed_running",
    MRL_感知力核心: "active",
    MRL_多世界同步: "active",
    MRL_回放回復: "active",
    MRL_主權層: "active"
  }
};
app.get("/health", (req, res) => {
  res.json({
    ok: true,
    ...MRL_STATE
  });
});
app.get("/mrl/state", (req, res) => {
  res.json(MRL_STATE);
});
// Read-only convergence governance view（規格見 docs/MRL_Runtime_Civilization_Stack_Convergence_v1.md）。
// 不啟動 daemon、不變更 runtime、不宣稱 pending 項目完成。
const MRL_CONVERGENCE_VIEW = {
  status: "SPEC_READY",
  implementation: "READ_ONLY_API_ACTIVE",
  source: "docs/MRL_Runtime_Civilization_Stack_Convergence_v1.md",
  merge_order: ["#35", "#37", "#36", "EntryGateway", "Convergence"],
  active: {
    runtime_core: "LOCAL_ACCEPTANCE",
    naming_alignment: "LOCAL_ACCEPTANCE",
    pid_scope: "DECLARED_ACTIVE",
    entry_gateway: "DECLARED_ACTIVE"
  },
  pending: {
    persistent_loop_daemon: "PENDING",
    replay_restore_runtime: "PENDING",
    world_sync: "PENDING",
    baseworld_db: "PENDING",
    dl580_reboot_survival: "PENDING"
  },
  note: "This endpoint is read-only convergence governance view. It does not start daemon, mutate runtime, or claim pending items complete."
};
app.get("/api/mrl/runtime/convergence", (req, res) => {
  res.json(MRL_CONVERGENCE_VIEW);
});
app.post("/mrl/perceive", (req, res) => {
  res.json({
    ok: true,
    route: "MRL_感知力核心",
    input: req.body,
    flow: [
      "世界狀態",
      "感知力場",
      "語境同步",
      "記憶拉取",
      "人格共振",
      "運轉組裝",
      "世界投影",
      "回放",
      "回復",
      "驗證",
      "重新同步"
    ],
    sovereignty: "MRL 主體；外部僅 Adapter"
  });
});
const port = process.env.MRL_PORT || 8790;
app.listen(port, () => {
  console.log(`MRL Runtime running on port ${port}`);
});
