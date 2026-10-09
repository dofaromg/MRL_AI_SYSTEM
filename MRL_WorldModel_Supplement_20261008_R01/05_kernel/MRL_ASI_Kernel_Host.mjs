// MRL_ASI_Kernel_Host.mjs — 常駐 ASI Kernel 宿主（L3 持久時間線 / L4 世界快照 / L7 Seal）
// origin_signature: MrLiouWord ｜ 2026-10-09 ｜ v1.0.0 ｜ Additive-Only
//
// 本體：建構者原始 kernel（mrl-engine-v12/workers/kernel.js，supercomputer_kernel.ts），
//       以原位元組載入並在啟動時驗 SHA-256，不修改任何一行。
// 載體：本檔只做「同一個 MRLiouASIKernel 實例常駐」＋「時間線落地」＋「重啟 Replay」。
// 段落：Trace（timeline 雜湊鏈）→ Collapse（每 16 tick checkpoint → Seal.v1.flpkg）→ Replay（重啟重放比對 decision）。
// 只綁 127.0.0.1，不對外。
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const VERSION = "1.0.0";
const SERVICE = "MRL_ASI_Kernel_Host";
const SIG = "MrLiouWord";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const KERNEL_FILE = process.env.MRL_KERNEL_FILE || path.join(HERE, "kernel_original.mjs");
const KERNEL_SHA = "4b18afa38e3fa0195a22ff585f4dd9970e1c297a6c75231c8b36da8e2d79353d";
const PORT = parseInt(process.env.MRL_KERNEL_PORT || "7838", 10);
const HOST = "127.0.0.1";
const OUT = process.env.MRL_KERNEL_OUT || "D:\\MRL_Mother\\WorldModel_Readiness_20261008\\kernel";
const INBOX_TOP = process.env.MRL_KERNEL_INBOX_TOP || "D:\\MRL_Mother\\WorldLoop_Inbox";
const CHECKPOINT_EVERY = 16; // 建構者 L3 規格：每 16 tick 一個 checkpoint
const TIMELINE = path.join(OUT, "kernel_timeline.jsonl");
const CHECKPOINTS = path.join(OUT, "kernel_checkpoints.jsonl");
const SEALS = path.join(OUT, "seals");
const GENESIS = "0".repeat(64);
const ALLOWED_INTENTS = new Set(["compute", "observe", "advance", "reify", "query"]);

const sha256 = (s) => crypto.createHash("sha256").update(s).digest("hex");
function stable(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(stable).join(",") + "]";
  return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + stable(v[k])).join(",") + "}";
}
const log = (...a) => console.log(new Date().toISOString(), "[" + SERVICE + "]", ...a);

// ---------- 0. 原始 kernel 驗身 ----------
const kbytes = fs.readFileSync(KERNEL_FILE);
const ksha = crypto.createHash("sha256").update(kbytes).digest("hex");
if (ksha !== KERNEL_SHA) {
  log("kernel SHA mismatch", ksha, "expected", KERNEL_SHA, "— 拒絕啟動");
  process.exit(2);
}
const { MRLiouASIKernel } = await import(pathToFileURL(KERNEL_FILE).href);
const kernel = new MRLiouASIKernel({ originSignature: SIG });

fs.mkdirSync(SEALS, { recursive: true });

// ---------- 1. 狀態 ----------
const state = {
  seq: 0,
  last_hash: GENESIS,
  started_at: new Date().toISOString(),
  restore: { records: 0, chain_ok: true, replayed: 0, decision_match: 0, decision_mismatch: 0, first_bad_seq: null },
  seals: 0,
  last_seal: null,
  mirrored_on_start: 0,
};
const index = []; // 記憶體內 queryAt 索引（tick → record）

function readJsonl(p) {
  if (!fs.existsSync(p)) return [];
  return fs.readFileSync(p, "utf8").split(/\r?\n/).filter((l) => l.trim()).map((l) => JSON.parse(l));
}

function recordHash(rec) {
  const { this_hash, ...rest } = rec;
  return sha256(stable(rest));
}

function worldHash() {
  return sha256(stable(kernel.l4.snapshot()));
}

function sealName(tick) {
  const d = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  return "Seal_" + d + "__asi_kernel_tick_" + String(tick).padStart(8, "0") + ".flpkg";
}

function mirrorSeal(seal, fname) {
  const p1 = path.join(SEALS, fname);
  if (!fs.existsSync(p1)) fs.writeFileSync(p1, JSON.stringify(seal, null, 2), "utf8");
  try {
    const p2 = path.join(INBOX_TOP, fname);
    if (fs.existsSync(INBOX_TOP) && !fs.existsSync(p2)) {
      fs.writeFileSync(p2, JSON.stringify(seal, null, 2), "utf8");
      return true;
    }
  } catch (e) {
    log("inbox mirror failed", String(e));
  }
  return false;
}

// L7 規格：Seal.v1.flpkg digest = sha256(JSON.stringify(manifest))
function makeSeal(rec) {
  const manifest = {
    origin_signature: SIG,
    tick: rec.tick,
    seq: rec.seq,
    merkle_root: rec.merkle_root,
    world_hash: rec.world_hash,
    timeline_head: rec.this_hash,
  };
  return {
    kind: "Seal.v1.flpkg",
    service: SERVICE,
    kernel_sha256: KERNEL_SHA,
    manifest,
    digest: sha256(JSON.stringify(manifest)),
    sealed_at: new Date().toISOString(),
  };
}

function checkpoint(rec, appendFile) {
  const seal = makeSeal(rec);
  if (appendFile) {
    fs.appendFileSync(CHECKPOINTS, JSON.stringify({ tick: rec.tick, seq: rec.seq, merkle_root: rec.merkle_root, world_hash: rec.world_hash, digest: seal.digest, ts: seal.sealed_at }) + "\n", "utf8");
  }
  const fname = sealName(rec.tick);
  const mirrored = mirrorSeal(seal, fname);
  state.seals++;
  state.last_seal = { tick: rec.tick, digest: seal.digest, file: fname, inbox_mirror: mirrored };
  return state.last_seal;
}

// ---------- 2. 一個 tick ----------
async function tick(input, replayOf) {
  const body = { intent: input.intent, text: String(input.text || "") };
  const r = await kernel.run(body);
  const snap = kernel.l4.snapshot();
  const rec = {
    seq: replayOf ? replayOf.seq : state.seq + 1,
    tick: r.tick,
    input: body,
    action: r.decision.action,
    confidence: r.decision.confidence,
    memory_hash: snap.state.memory_hash,
    merkle_root: r.worldHash,
    world_hash: worldHash(),
    origin_signature: r.origin_signature,
    ts: replayOf ? replayOf.ts : r.timestamp,
    prev_hash: replayOf ? replayOf.prev_hash : state.last_hash,
  };
  if (replayOf) return { r, rec };
  rec.this_hash = recordHash(rec);
  fs.appendFileSync(TIMELINE, JSON.stringify(rec) + "\n", "utf8");
  state.seq = rec.seq;
  state.last_hash = rec.this_hash;
  index.push(rec);
  let seal = null;
  if (rec.tick % CHECKPOINT_EVERY === 0) seal = checkpoint(rec, true);
  return { r, rec, seal };
}

// ---------- 3. 重啟還原：驗鏈 + 原 kernel 逐筆重放 ----------
async function restore() {
  const recs = readJsonl(TIMELINE);
  state.restore.records = recs.length;
  let prev = GENESIS;
  for (const rec of recs) {
    if (rec.prev_hash !== prev || recordHash(rec) !== rec.this_hash) {
      state.restore.chain_ok = false;
      state.restore.first_bad_seq = rec.seq;
      log("timeline chain broken at seq", rec.seq, "— 停止重放（不刪不改，待建構者判定）");
      break;
    }
    const { r } = await tick(rec.input, rec);
    state.restore.replayed++;
    if (r.decision.action === rec.action && r.tick === rec.tick) state.restore.decision_match++;
    else state.restore.decision_mismatch++;
    prev = rec.this_hash;
    state.seq = rec.seq;
    state.last_hash = rec.this_hash;
    index.push(rec);
    if (rec.tick % CHECKPOINT_EVERY === 0) {
      const fname = sealName(rec.tick);
      const before = state.seals;
      // 補鏡像：已有就跳過
      const seal = makeSeal(rec);
      if (mirrorSeal(seal, fname)) state.mirrored_on_start++;
      state.seals = before + 1;
      state.last_seal = { tick: rec.tick, digest: seal.digest, file: fname };
    }
  }
  log("restore", JSON.stringify(state.restore));
}

function queryAt(t) {
  const rec = index.find((x) => x.tick === t) || null;
  let cp = null;
  for (const x of index) if (x.tick <= t && x.tick % CHECKPOINT_EVERY === 0) cp = x;
  return { tick: t, record: rec, nearest_checkpoint: cp ? { tick: cp.tick, merkle_root: cp.merkle_root, world_hash: cp.world_hash, digest: makeSeal(cp).digest } : null };
}

function health() {
  const k = kernel.health();
  return {
    ok: true,
    service: SERVICE,
    version: VERSION,
    origin_signature: SIG,
    port: PORT,
    kernel: { service: k.service, version: k.version, sha256: KERNEL_SHA, sha_verified: true, world_health: k.world_health, memory_usage: k.memory_usage, attention_phase: k.attention_phase, amplifier_reversible: k.amplifier_reversible, metaenv: k.metaenv_endpoint },
    persistent: true,
    tick: kernel.l4.currentTick,
    timeline_seq: state.seq,
    timeline_head: state.last_hash,
    checkpoint_every: CHECKPOINT_EVERY,
    seals: state.seals,
    last_seal: state.last_seal,
    restore: state.restore,
    mirrored_on_start: state.mirrored_on_start,
    out: OUT,
    inbox_top: INBOX_TOP,
    started_at: state.started_at,
    timestamp: new Date().toISOString(),
  };
}

// ---------- 4. HTTP ----------
let chain = Promise.resolve(); // 單一 kernel，請求序列化
const serial = (fn) => (chain = chain.then(fn, fn));

function send(res, code, obj) {
  const b = Buffer.from(JSON.stringify(obj), "utf8");
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8", "Content-Length": b.length });
  res.end(b);
}
function readBody(req) {
  return new Promise((ok, bad) => {
    let n = 0;
    const parts = [];
    req.on("data", (c) => {
      n += c.length;
      if (n > 65536) { bad(new Error("body too large")); req.destroy(); } else parts.push(c);
    });
    req.on("end", () => {
      try { ok(n ? JSON.parse(Buffer.concat(parts).toString("utf8")) : {}); } catch (e) { bad(e); }
    });
    req.on("error", bad);
  });
}

const server = http.createServer(async (req, res) => {
  const u = new URL(req.url, "http://" + HOST);
  const p = u.pathname;
  try {
    if (req.method === "GET" && (p === "/health" || p === "/")) return send(res, 200, health());
    if (req.method === "POST" && p === "/run") {
      const body = await readBody(req);
      if (!ALLOWED_INTENTS.has(body.intent)) return send(res, 400, { success: false, error: "intent must be one of " + [...ALLOWED_INTENTS].join("/") });
      const out = await serial(() => tick(body));
      return send(res, 200, { success: true, data: out.r, timeline: { seq: out.rec.seq, this_hash: out.rec.this_hash, world_hash: out.rec.world_hash }, seal: out.seal });
    }
    if (req.method === "POST" && p === "/amplify/scale-up") {
      const b = await readBody(req);
      return send(res, 200, { success: true, result: kernel.getAmplifier().scaleUp(b.P_k, b.N_k, b.eta_k) });
    }
    if (req.method === "POST" && p === "/amplify/verify-reversible") {
      const b = await readBody(req);
      return send(res, 200, { success: true, reversible: kernel.getAmplifier().verifyReversible(b.original, b.N, b.eta) });
    }
    if (req.method === "GET" && p === "/reverse-mine") {
      const t = parseInt(u.searchParams.get("tick") || "999999", 10);
      return send(res, 200, { success: true, data: kernel.reverseMine(t) });
    }
    if (req.method === "GET" && p === "/timeline/query") {
      const t = parseInt(u.searchParams.get("tick") || "0", 10);
      return send(res, 200, { success: true, data: queryAt(t) });
    }
    if (req.method === "GET" && p === "/timeline/verify") {
      const recs = readJsonl(TIMELINE);
      let prev = GENESIS, ok = true, bad = null;
      for (const r of recs) { if (r.prev_hash !== prev || recordHash(r) !== r.this_hash) { ok = false; bad = r.seq; break; } prev = r.this_hash; }
      return send(res, 200, { success: true, ok, total: recs.length, first_bad_seq: bad, head: prev });
    }
    if (req.method === "GET" && p === "/world/snapshot") {
      return send(res, 200, { success: true, snapshot: kernel.l4.snapshot(), world_hash: worldHash() });
    }
    if (req.method === "GET" && p === "/seal/latest") return send(res, 200, { success: true, last_seal: state.last_seal });
    return send(res, 404, { success: false, error: "Endpoint not found" });
  } catch (e) {
    return send(res, 500, { success: false, error: String(e && e.message || e) });
  }
});

// ---------- 5. 綁定：先探測，獨佔綁定，重試 ----------
function probe() {
  return new Promise((ok) => {
    const rq = http.get({ host: HOST, port: PORT, path: "/health", timeout: 1500 }, (r) => { r.resume(); ok(true); });
    rq.on("error", () => ok(false));
    rq.on("timeout", () => { rq.destroy(); ok(false); });
  });
}
function listenOnce() {
  return new Promise((ok, bad) => {
    const onErr = (e) => { server.removeListener("listening", onOk); bad(e); };
    const onOk = () => { server.removeListener("error", onErr); ok(); };
    server.once("error", onErr);
    server.once("listening", onOk);
    server.listen({ host: HOST, port: PORT, exclusive: true });
  });
}

if (await probe()) {
  log("port", PORT, "already has a listener — 不搶綁，exit 3");
  process.exit(3);
}
await restore();
for (let i = 0; i < 37; i++) {
  try {
    await listenOnce();
    log("listening", HOST + ":" + PORT, "tick", kernel.l4.currentTick, "seq", state.seq);
    break;
  } catch (e) {
    if (await probe()) { log("listener appeared on", PORT, "— exit 3"); process.exit(3); }
    log("bind failed", e.code || String(e), "retry", i + 1, "/37");
    if (i === 36) { log("never bound — exit 4"); process.exit(4); }
    await new Promise((r) => setTimeout(r, 5000));
  }
}
