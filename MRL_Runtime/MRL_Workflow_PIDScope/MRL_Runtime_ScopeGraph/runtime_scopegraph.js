"use strict";
// MRL_Runtime_ScopeGraph — runtime scope graph + inheritance/dependency edges
// origin_signature=MrLiouWord

const SCOPES = {
  MRL_RuntimeScope: ["MetaIR", "ParticleIR", "RuntimeGraph", "Verification"],
  MRL_ReplayScope: ["checkpoint", "restore", "rollback", "replay"],
  MRL_WorldScope: ["world_runtime", "parallel_world", "context_synchronization"],
  MRL_ExternalScope: ["cloudflared", "xoopz", "github_mirror", "external_adapters"],
};

class RuntimeScopeGraph {
  constructor() {
    this.nodes = new Map(); // runtime_id -> scope
    this.edges = [];        // [from_runtime_id, to_runtime_id]
  }

  addNode(runtime_id, scope) {
    if (!SCOPES[scope]) throw new Error("unknown scope: " + scope);
    const prev = this.nodes.get(runtime_id);
    this.nodes.set(runtime_id, scope);
    return { runtime_id, scope, rebound: !!prev && prev !== scope };
  }

  addEdge(from, to) { this.edges.push([from, to]); return [from, to]; }

  scopeOf(runtime_id) { return this.nodes.get(runtime_id) || null; }

  snapshot() {
    return { nodes: [...this.nodes.entries()], edges: this.edges.map((e) => [e[0], e[1]]) };
  }

  restore(snap) {
    this.nodes = new Map(snap.nodes.map((n) => [n[0], n[1]]));
    this.edges = snap.edges.map((e) => [e[0], e[1]]);
  }
}

module.exports = { RuntimeScopeGraph, SCOPES };
