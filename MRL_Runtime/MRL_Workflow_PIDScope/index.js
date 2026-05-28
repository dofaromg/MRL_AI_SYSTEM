"use strict";
// MRL_Workflow_PIDScope — Runtime Workflow Ownership Layer (facade)
// origin_signature=MrLiouWord
//
// Layer B (Node orchestration ownership). 接 DB adapter（本地 acceptance / 正式 MRL_BaseWorld_DB_v1）。
// 提供：PID ownership、workflow registry、scope graph、process lineage、scope isolation、
//       recovery（checkpoint/restore）、persistent-loop orchestration。

const { makeAdapter, TABLES } = require("./db_adapter");
const { PIDScopeCore } = require("./MRL_PIDScope_Core/pidscope_core");
const { WorkflowRegistry } = require("./MRL_Workflow_Registry/workflow_registry");
const { RuntimeScopeGraph, SCOPES } = require("./MRL_Runtime_ScopeGraph/runtime_scopegraph");
const { ProcessLineage } = require("./MRL_ProcessLineage/process_lineage");
const { ScopeIsolation } = require("./MRL_ScopeIsolation/scope_isolation");
const { RuntimeRecovery } = require("./MRL_Runtime_Recovery/runtime_recovery");
const { OrchestrationPIDBridge } = require("./MRL_Orchestration_PIDBridge/orchestration_pidbridge");

function createPIDScopeLayer(opts) {
  opts = opts || {};
  const db = makeAdapter(opts.dbTarget);
  const core = new PIDScopeCore(db);
  const registry = new WorkflowRegistry(db);
  const graph = new RuntimeScopeGraph();
  const lineage = new ProcessLineage(db);
  const isolation = new ScopeIsolation(db, graph, core);
  const recovery = new RuntimeRecovery(db, graph);
  const orchestrator = new OrchestrationPIDBridge(core, recovery, opts.spawnArgs);
  return {
    origin_signature: "MrLiouWord",
    runtime_layer: "MRL_Mother_Runtime",
    db, core, registry, graph, lineage, isolation, recovery, orchestrator,
    SCOPES, TABLES,
  };
}

module.exports = { createPIDScopeLayer, SCOPES, TABLES };
