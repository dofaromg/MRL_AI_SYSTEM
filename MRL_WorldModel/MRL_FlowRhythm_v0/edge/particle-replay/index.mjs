// particle-replay · 補位 FlowRhythm 節奏重播（SUPPLEMENT_EXISTING）
// origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來 ｜ Additive-Only
//
// 既有 particle-replay（L7-Meta，v1.0.0，version cf8ef762…）原碼一字不改，原路由全部照舊；
// 只新增 /rhythm/* —— 真正的 Jump → Collapse → Trace → Replay 重播，
// 引擎與本體 flow_rhythm.py v0.2.0 逐位元組一致，不依賴 DL580 bridge（bridge 斷線時照樣能重播）。
// 原碼 shell-deploy.js 不入 repo（內含 bridge 金鑰），由 deploy.sh 部署時從線上當前版本取回。
import original from "./shell-deploy.js";
import * as Rhythm from "../flow_rhythm.mjs";
import LEX from "../lexicon.v0.2.0.json";

let _L = null;
const lex = () => (_L ||= Rhythm.prepareLexicon(LEX));
const H = { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*",
  "X-Particle": "replay", "X-Layer": "L7-Meta", "X-Origin": Rhythm.SIGN };
const j = (d, s = 200) => new Response(JSON.stringify(d, null, 2), { status: s, headers: H });

async function rhythm(req, u) {
  const p = u.pathname;
  if (p === "/rhythm" || p === "/rhythm/") {
    return j({ particle: "particle-replay", supplement: "FlowRhythm v" + Rhythm.ENGINE_VERSION,
      origin_signature: Rhythm.SIGN, body: "flow_rhythm.py（本體，權威）", carrier: "edge JS（逐位元組一致）",
      endpoints: { "POST /rhythm/replay": "v0.2.0 軌跡 → 重建粒子鏈、封包、逐位元組比對",
        "POST /rhythm/run": "粒子語句 .fltnz → Jump→Collapse→Trace 軌跡" },
      gate: "預設正典 fail-closed；?sandbox=1 才允許 PROVISIONAL_NOT_CANONICAL 映射",
      lexicon_sources_sha256: LEX.source_sha256 });
  }
  if (req.method !== "POST") return j({ ok: false, error: "POST text/plain" }, 405);
  const text = await req.text();
  const allowProvisional = u.searchParams.get("sandbox") === "1";
  const title = u.searchParams.get("title") || "語場節奏";
  try {
    const L = lex();
    const r = p === "/rhythm/replay" ? await Rhythm.replay(text, L, { title, allowProvisional })
      : p === "/rhythm/run" ? await Rhythm.run(Rhythm.chainFromFltnz(text), L, { title, allowProvisional })
      : null;
    if (!r) return j({ ok: false, error: "not found", path: p }, 404);
    return j({ ok: true, engine_version: Rhythm.ENGINE_VERSION, semantic_status: r.semantic_status,
      provisional_mappings: r.provisional_mappings, final_sha256: r.final_sha256,
      byte_identical: r.byte_identical, trace_ops: r.trace_ops, chain: r.chain, packets: r.field.packets,
      trace_fltnz: r.trace_fltnz, narration: r.narration, origin_signature: Rhythm.SIGN });
  } catch (e) {
    return j({ ok: false, error: e.name, reason: e.message,
      header: p === "/rhythm/replay" ? Rhythm.traceHeaderInfo(text) : undefined }, 422);
  }
}

export default {
  async fetch(req, env, ctx) {
    const u = new URL(req.url);
    if (u.pathname === "/rhythm" || u.pathname.startsWith("/rhythm/")) {
      if (req.method === "OPTIONS") return new Response(null, { headers: H });
      return rhythm(req, u);
    }
    return original.fetch(req, env, ctx);   // 既有路由照舊
  },
};
