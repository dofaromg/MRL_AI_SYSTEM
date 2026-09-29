"""
FlowRhythm v0 驗收 —— 全部用建構者自己的語料（2025-07 粒子字典ai/工程師給的）
  A. 同一顆種子的兩種形式（EchoPersona.pcode 與 EchoPersona.Sample.v1.flpkg）展開成同一條粒子鏈
  B. 敘述輸出與建構者 FluinSim runtime.log（Group1、Group2）逐位元組相同
  C. Jump → Collapse → Trace → Replay：只讀軌跡重建，封包雜湊一致、軌跡逐位元組重現
  D. 軌跡 .fltnz 可被 mrl Dialect 逐位元組往返，並被辨識為 trace 行
  E. 母體所有種子（pcode / fltnz / flpkg / flseed）都能跑完節奏並 Replay
  F. 世界圖：把節奏軌跡放回母體語料，套用可見律（Node + Map + Trace + Coupling）
  G. 未經核准的詞性／階段→軌跡動詞映射在正典模式 fail-closed；sandbox 明示啟用並標記非正典
origin_signature: MrLiouWord
"""
import glob, json, os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import flow_rhythm as F
D = F.D
L = F.load_lexicon()
LEX = F.LEX_DIR
FIX = "2025-07-23T19:41:36.746707Z"   # 取 FluinSim 封裝時間當固定時鐘（可重現）
res = {}

# A
c_pcode, meta = F.load_seed(os.path.join(LEX, "下載 EchoPersona.pcode"), L)
c_flpkg, _ = F.load_seed(os.path.join(LEX, "下載 EchoPersona.Sample.v1.flpkg"), L)
res["A_same_chain_pcode_vs_flpkg"] = c_pcode == c_flpkg and not meta["unmapped"]

# B
with zipfile.ZipFile(os.path.join(LEX, "重新下載 FluinSim.DualSet.v1.flsim")) as z:
    for g in ("Group1_EchoPersona", "Group2_ConflictChange"):
        chain = F.chain_from_fltnz(z.read(g + ".fltnz").decode("utf-8"))
        log = z.read(g + ".runtime.log").decode("utf-8")
        res[f"B_{g}_narration_byte_identical"] = F.narrate_like_flsim(chain, L) == log

# C + D + G
try:
    F.run(c_pcode, L, F.Clock(FIX), "EchoPersona")
except F.ProvisionalSemanticMappingError:
    res["G_canonical_default_fail_closed"] = True
else:
    res["G_canonical_default_fail_closed"] = False

r = F.run(c_pcode, L, F.Clock(FIX), "EchoPersona", allow_provisional=True)
res["G_sandbox_marked_noncanonical"] = (
    r["semantic_status"] == F.SEMANTIC_PROVISIONAL
    and bool(r["provisional_mappings"])
    and "semantic_status: PROVISIONAL_NOT_CANONICAL" in r["trace_fltnz"]
)
hash_payload = {k: r["field"][k] for k in (
    "persona", "attributes", "objects", "jumps", "flows", "targets", *F.HASH_POLICY_FIELDS
)}
verified_payload = dict(hash_payload)
verified_payload["semantic_status"] = F.SEMANTIC_VERIFIED
verified_payload["provisional_mappings"] = []
res["G_authority_state_bound_to_final_sha256"] = (
    F.packet_hash(hash_payload) == r["final_sha256"]
    and F.packet_hash(verified_payload) != r["final_sha256"]
)
rp = F.replay(r["trace_fltnz"], L, "EchoPersona", allow_provisional=True)
res["C_replay_same_packet_sha256"] = rp["final_sha256"] == r["final_sha256"]
res["C_replay_trace_byte_identical"] = rp["trace_fltnz"] == r["trace_fltnz"]
ok, ir = D.roundtrip(r["trace_fltnz"].encode("utf-8"), "EchoPersona.trace.fltnz")
res["D_dialect_roundtrip"] = ok
res["D_trace_ops"] = sum(1 for o in D.parse_ir(ir).ops if o.kind == "trace")

# E
seeds = [os.path.join(LEX, n) for n in ("下載 EchoPersona.pcode", "下載 EchoPersona.Sample.v1.flpkg",
         "下載 FluinCoreSeed.v1.flseed", "下載 Memory.Seed.Core.v1.flseed")]
with zipfile.ZipFile(os.path.join(LEX, "重新下載 FluinSim.DualSet.v1.flsim")) as z:
    extra = {g: z.read(g + ".fltnz").decode("utf-8") for g in ("Group1_EchoPersona", "Group2_ConflictChange")}
out_dir = os.path.join(ROOT, "traces"); os.makedirs(out_dir, exist_ok=True)
runs = []
for p in seeds:
    ch, _ = F.load_seed(p, L); runs.append((os.path.basename(p).replace("下載 ", ""), ch))
for g, t in extra.items():
    runs.append((g, F.chain_from_fltnz(t)))
e_ok = True
for name, ch in runs:
    r1 = F.run(ch, L, F.Clock(FIX), name, allow_provisional=True)
    r2 = F.replay(r1["trace_fltnz"], L, name, allow_provisional=True)
    good = r2["final_sha256"] == r1["final_sha256"] and r2["trace_fltnz"] == r1["trace_fltnz"]
    e_ok &= good
    stem = name.rsplit(".", 1)[0] if name.endswith((".pcode", ".flpkg", ".flseed")) else name
    open(os.path.join(out_dir, stem + ".trace.fltnz"), "w", encoding="utf-8", newline="\n").write(r1["trace_fltnz"])
    print(f"  {name:36s} {len(ch)} 粒子  封包 {r1['final_sha256'][:16]}  Replay {'PASS' if good else 'FAIL'}")
res["E_all_seeds_replay"] = e_ok
res["E_seed_count"] = len(runs)

# F
sys.path.insert(0, os.path.join(F.REPO, "MRL_WorldModel", "MRL_Dialect_v0"))
import mrl_world_graph as W
src = os.path.join(F.REPO, "MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1")
if not os.path.isdir(src):
    src = F.LEX_DIR   # DL580 sparse 展開時用語意字典副本
before = W.build([src])
after = W.build([src, out_dir])
res["F_visible_before"] = before["tiers"].get("visible", 0)
res["F_visible_after"] = after["tiers"].get("visible", 0)
res["F_visible_nodes"] = [n["id"] for n in after["visible_nodes"]]

print(json.dumps(res, ensure_ascii=False, indent=1))
bools = [v for k, v in res.items() if isinstance(v, bool)]
sys.exit(0 if all(bools) else 1)
