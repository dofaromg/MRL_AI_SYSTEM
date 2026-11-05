// FlowRhythm edge 載體一致性驗收（JS ⇄ 本體 Python v0.2.0）
// origin_signature: MrLiouWord
// 用法：node conformance.mjs   （需 python3；全部輸出寫入系統臨時目錄並清除）
//   H. JS run 與 Python run（同固定時鐘）軌跡、封包、敘述逐位元組相同（6 顆母體種子）
//   I. JS Replay 讀 Python 軌跡：逐位元組重現、封包雜湊一致
//   J. Python Replay 讀 JS 軌跡：逐位元組重現（反向）
//   K. 語義 Gate：正典預設 fail-closed；竄改 status / 刪授權行 / 竄改映射 → Replay 拒絕
//   L. v0.1.0 歷史軌跡：判讀為歷史證據，正典 Replay 拒絕；traces/ 前後 SHA-256 不變
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as R from "./flow_rhythm.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const TRACES = join(HERE, "..", "traces");
const treeHash = () => Object.fromEntries(readdirSync(TRACES).sort()
  .map((n) => [n, createHash("sha256").update(readFileSync(join(TRACES, n))).digest("hex")]));
const before = treeHash();

const L = R.prepareLexicon(JSON.parse(readFileSync(join(HERE, `lexicon.v${R.ENGINE_VERSION}.json`), "utf8")));
const tmp = mkdtempSync(join(tmpdir(), "mrl-flowrhythm-edge-"));
const res = {};
try {
  const refPath = join(tmp, "ref.json");
  execFileSync("python3", [join(HERE, "dump_reference.py"), refPath], { stdio: "inherit" });
  const ref = JSON.parse(readFileSync(refPath, "utf8"));

  let h = true, i = true; const jsTraces = [];
  for (const r of ref.runs) {
    const chain = r.fltnz_source ? R.chainFromFltnz(r.fltnz_source) : r.chain;
    const sameChain = JSON.stringify(chain) === JSON.stringify(r.chain);
    const js = await R.run(chain, L, { clock: new R.Clock({ fixed: ref.fixed_clock }), title: r.name, allowProvisional: true });
    const okH = sameChain && js.trace_fltnz === r.trace_fltnz && js.final_sha256 === r.final_sha256
      && js.narration === r.narration && JSON.stringify(js.field.packets) === JSON.stringify(r.packets);
    const rp = await R.replay(r.trace_fltnz, L, { title: r.name, allowProvisional: true });
    const okI = rp.byte_identical && rp.final_sha256 === r.final_sha256;
    h &&= okH; i &&= okI;
    jsTraces.push({ name: r.name, trace: js.trace_fltnz, final_sha256: js.final_sha256 });
    console.log(`  ${r.name.padEnd(34)} ${String(chain.length).padStart(2)} 粒子  封包 ${js.final_sha256.slice(0, 16)}  run=${okH ? "PASS" : "FAIL"}  replay=${okI ? "PASS" : "FAIL"}`);
  }
  res.H_js_run_byte_identical_to_python = h;
  res.I_js_replay_python_traces = i;
  res.HI_seed_count = ref.runs.length;

  const jsPath = join(tmp, "js_traces.json");
  writeFileSync(jsPath, JSON.stringify(jsTraces));
  const back = JSON.parse(execFileSync("python3", [join(HERE, "python_replay_check.py"), jsPath], { encoding: "utf8" }));
  res.J_python_replay_js_traces = Object.values(back).length === ref.runs.length && Object.values(back).every(Boolean);

  // K
  const echo = ref.runs[0];
  try { await R.run(echo.chain, L); res.K_canonical_default_fail_closed = false; }
  catch (e) { res.K_canonical_default_fail_closed = e instanceof R.ProvisionalSemanticMappingError; }
  const t = echo.trace_fltnz;
  const tampered = {
    status: t.replace("semantic_status: PROVISIONAL_NOT_CANONICAL", "semantic_status: VERIFIED"),
    missing: t.split("\n").filter((l) => !l.startsWith("# mrl_semantic_authority: ")).join("\n"),
    mappings: t.replace(/"provisional_mappings":\[[^\]]*\]/, '"provisional_mappings":[]'),
  };
  for (const [k, v] of Object.entries(tampered)) {
    try { await R.replay(v, L, { allowProvisional: true }); res[`K_rejects_tampered_${k}`] = false; }
    catch (e) { res[`K_rejects_tampered_${k}`] = e instanceof R.SemanticAuthorityIntegrityError; }
  }
  try { await R.replay(t, L); res.K_canonical_replay_fail_closed = false; }
  catch (e) { res.K_canonical_replay_fail_closed = e instanceof R.ProvisionalSemanticMappingError; }

  // L
  let hist = true;
  for (const n of readdirSync(TRACES)) {
    const txt = readFileSync(join(TRACES, n), "utf8");
    const info = R.traceHeaderInfo(txt);
    let rejected = false;
    try { await R.replay(txt, L, { allowProvisional: true }); } catch (e) { rejected = e instanceof R.SemanticAuthorityIntegrityError; }
    hist &&= info.historical === true && info.engine_version === "0.1.0" && rejected;
  }
  res.L_v010_historical_recognized_and_not_replayed_as_v020 = hist;

} finally {
  rmSync(tmp, { recursive: true, force: true });
}
res.L_historical_traces_untouched = JSON.stringify(before) === JSON.stringify(treeHash());
console.log(JSON.stringify(res, null, 1));
process.exit(Object.values(res).every((v) => typeof v !== "boolean" || v) ? 0 : 1);
