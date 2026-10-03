// MRL FlowRhythm v0 —— 邊緣載體（JS）
// origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來 ｜ Additive-Only
//
// 權位：載體。承載本體 flow_rhythm.py 的 Jump → Collapse → Trace → Replay，
//       逐行對照 Python v0.2.0；Python 為權威，本檔只能與它逐位元組一致，不得自行定義語意。
// 語意字典：lexicon.v0.2.0.json（由 build_lexicon_json.py 從建構者 2025-07 原檔匯出）。
// 語義 Gate：與 Python 相同 —— 正典預設 fail-closed，sandbox 須明示 allowProvisional。

export const ENGINE_VERSION = "0.2.0";
export const SIGN = "MrLiouWord";
export const SEMANTIC_VERIFIED = "VERIFIED";
export const SEMANTIC_PROVISIONAL = "PROVISIONAL_NOT_CANONICAL";
const HASH_POLICY_FIELDS = ["semantic_status", "provisional_mappings"];

export class ProvisionalSemanticMappingError extends Error {
  constructor(m) { super(m); this.name = "ProvisionalSemanticMappingError"; }
}
export class SemanticAuthorityIntegrityError extends Error {
  constructor(m) { super(m); this.name = "SemanticAuthorityIntegrityError"; }
}

// 與 mrl_dialect.RE_TRACE 相同
const RE_TRACE = /^(\s*)\[(\d{4}-\d{2}-\d{2}T[^\]]*)\](\s*)::([^\s→:]+)(→|->)(\s*)(.*?)(\s*)$/u;

export function prepareLexicon(doc) {
  if (doc.engine_version !== ENGINE_VERSION || doc.origin_signature !== SIGN) {
    throw new SemanticAuthorityIntegrityError("lexicon engine_version / origin_signature mismatch");
  }
  return {
    module_map: doc.module_map,
    kind: doc.kind,
    pcode_to_code: doc.pcode_to_code,            // 有序配對
    verb_of: doc.verb_of,
    verified: new Set(doc.verified_verb_kinds),
    source_sha256: doc.source_sha256,
  };
}

// ── 粒子語句 .fltnz → 粒子鏈（同 chain_from_fltnz）
export function chainFromFltnz(text) {
  const out = [];
  for (const line of text.split(/\r\n|\r|\n/)) {   // ≈ str.splitlines()（常見換行）
    const s = line.split("#")[0].trim();
    if (!s || s.startsWith("//")) continue;
    out.push(s);
  }
  return out;
}

export function kindOf(tok, L) {
  if (tok.startsWith("⊕")) return "core";
  if (tok === "∴") return "logic";
  if (tok.startsWith("⊗")) return "target";
  return Object.prototype.hasOwnProperty.call(L.kind, tok) ? L.kind[tok] : "unknown";
}

export function semanticAuthority(chain, L) {
  const prov = new Set();
  for (const t of chain) {
    const k = kindOf(t, L);
    if (!Object.prototype.hasOwnProperty.call(L.verb_of, k)) {
      throw new SemanticAuthorityIntegrityError(`no verb mapping for particle kind: ${k}`);
    }
    if (!L.verified.has(k)) prov.add(`${k}->${L.verb_of[k]}`);
  }
  const provisional = [...prov].sort(cmpCodePoint);
  return {
    engine_version: ENGINE_VERSION,
    origin_signature: SIGN,
    semantic_status: provisional.length ? SEMANTIC_PROVISIONAL : SEMANTIC_VERIFIED,
    provisional_mappings: provisional,
  };
}

// Python sorted() 依 code point；JS 預設依 UTF-16，這裡改成 code point
function cmpCodePoint(a, b) {
  const A = [...a], B = [...b];
  for (let i = 0; i < Math.min(A.length, B.length); i++) {
    const d = A[i].codePointAt(0) - B[i].codePointAt(0);
    if (d) return d;
  }
  return A.length - B.length;
}

// json.dumps(ensure_ascii=False, sort_keys=True, separators=(",", ":"))
export function canonicalJson(v) {
  if (Array.isArray(v)) return "[" + v.map(canonicalJson).join(",") + "]";
  if (v && typeof v === "object") {
    return "{" + Object.keys(v).sort(cmpCodePoint)
      .map((k) => JSON.stringify(k) + ":" + canonicalJson(v[k])).join(",") + "}";
  }
  return JSON.stringify(v);   // 字串 / null / bool
}

export async function sha256Hex(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
export const packetHash = (p) => sha256Hex(canonicalJson(p));

// 時間戳：fixed 每拍 +1 微秒；seq 為 Replay 沿用原時間戳；否則當下 UTC（微秒補 000）
export class Clock {
  constructor({ fixed = null, seq = null } = {}) {
    this.seq = seq ? [...seq] : null;
    if (fixed) {
      const m = fixed.match(/^(.*T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?Z$/);
      if (!m) throw new Error("fixed clock must be ISO UTC …Z");
      this.base = Date.parse(m[1] + "Z");
      this.us = Number((m[2] || "0").padEnd(6, "0"));
    }
  }
  now() {
    if (this.seq && this.seq.length) return this.seq.shift();
    if (this.base === undefined) {
      const d = new Date().toISOString();           // …SS.mmmZ
      return d.slice(0, -1) + "000Z";
    }
    const ms = this.base + Math.floor(this.us / 1000);
    const s = new Date(ms).toISOString().slice(0, 19) + "." + String(this.us % 1e6).padStart(6, "0") + "Z";
    this.us += 1;
    return s;
  }
}

// ── 節奏執行：Jump → Collapse → Trace
export async function run(chain, L, { clock = new Clock(), title = "語場節奏", allowProvisional = false } = {}) {
  if (/[\r\n]/.test(title)) {
    throw new SemanticAuthorityIntegrityError("trace title must not contain CR/LF");
  }
  const authority = semanticAuthority(chain, L);
  const provisional = authority.provisional_mappings;
  if (provisional.length && !allowProvisional) {
    throw new ProvisionalSemanticMappingError(
      "canonical FlowRhythm refused provisional mappings: " + provisional.join(", "));
  }
  const status = authority.semantic_status;
  const f = { persona: null, attributes: [], objects: [], jumps: [], flows: [], targets: [],
    packets: [], origin_signature: SIGN, semantic_status: status, provisional_mappings: provisional };
  const pick = (keys) => Object.fromEntries(keys.map((k) => [k, f[k]]));
  const events = [];
  let pending = null;
  for (const tok of chain) {
    const k = kindOf(tok, L);
    const verb = L.verb_of[k];
    let detail = "";
    if (k === "core") f.persona = tok.split(":").slice(1).join(":").trim();
    else if (k === "adjective") f.attributes.push(tok);
    else if (k === "noun") f.objects.push(tok);
    else if (k === "logic") {                                   // Jump
      pending = { cause: [...f.attributes, ...f.objects], gate: tok };
      f.jumps.push(pending);
    } else if (k === "verb") {                                  // Collapse
      if (pending) { pending.effect = tok; pending = null; }
      f.flows.push(tok);
      const h = await packetHash(pick(["persona", "attributes", "objects", "jumps", "flows", ...HASH_POLICY_FIELDS]));
      f.packets.push({ flow: tok, sha256: h });
      detail = ` #${h.slice(0, 16)}`;
    } else if (k === "target") f.targets.push(tok);              // Trace
    events.push({ ts: clock.now(), verb, token: tok, kind: k, detail,
      mapping_status: L.verified.has(k) ? SEMANTIC_VERIFIED : SEMANTIC_PROVISIONAL,
      narration: L.module_map[tok] ?? "未知模組" });
  }
  const final = await packetHash(pick(["persona", "attributes", "objects", "jumps", "flows", "targets", ...HASH_POLICY_FIELDS]));
  const lines = [
    `# ${title} · FlowRhythm v${ENGINE_VERSION} · origin_signature: ${SIGN} · semantic_status: ${status}`,
    "# mrl_semantic_authority: " + canonicalJson(authority),
    "::initiated::",
    ...events.map((e) => `[${e.ts}] ::${e.verb}→ ${e.token}${e.detail}`),
  ];
  const body = chain.filter((t) => !t.startsWith("⊕"));
  if (body.length > 1) lines.push(body.join(" → "));             // Coupling
  for (const tok of chain) for (const [pc, code] of L.pcode_to_code) if (code === tok) lines.push(`⌬map[${pc}]↦${code}`);  // Map
  return { chain, field: f, events, final_sha256: final, semantic_status: status,
    provisional_mappings: provisional, trace_fltnz: lines.join("\n") + "\n",
    narration: events.map((e) => `[${e.token}] → ${e.narration}`).join("\n") };
}

// ── Replay：只讀軌跡，重建一切
export async function replay(traceText, L, { title = "語場節奏", allowProvisional = false } = {}) {
  const textLines = traceText.split(/\r\n|\r|\n/);
  if (textLines.length && textLines[textLines.length - 1] === "") textLines.pop();
  const ops = [];
  for (const line of textLines) {
    if (line.trim() === "") continue;
    const m = line.match(RE_TRACE);
    if (m) ops.push({ ts: m[2], verb: m[4], target: m[7] });
  }
  const chain = ops.map((o) => o.target.replace(/ #[0-9a-f]{16}$/, ""));
  const expected = semanticAuthority(chain, L);
  const header = textLines[0] || "";
  const sm = header.match(/semantic_status: ([A-Z_]+)/);
  const auth = textLines.filter((l) => l.startsWith("# mrl_semantic_authority: "));
  if (!sm || auth.length !== 1) throw new SemanticAuthorityIntegrityError("missing or duplicate semantic authority metadata");
  let serialized;
  try { serialized = JSON.parse(auth[0].split(": ").slice(1).join(": ")); }
  catch { throw new SemanticAuthorityIntegrityError("invalid semantic authority metadata"); }
  if (sm[1] !== expected.semantic_status || canonicalJson(serialized) !== canonicalJson(expected)) {
    throw new SemanticAuthorityIntegrityError("semantic authority metadata does not match replayed chain");
  }
  const r = await run(chain, L, { clock: new Clock({ seq: ops.map((o) => o.ts) }), title, allowProvisional });
  return { ...r, trace_ops: ops.length, byte_identical: r.trace_fltnz === traceText };
}

// 軌跡標頭判讀（給邊緣回報用；v0.1.0 歷史軌跡無語義授權行 → 歷史證據，不可正典 Replay）
export function traceHeaderInfo(traceText) {
  const h = traceText.split(/\r\n|\r|\n/)[0] || "";
  const v = h.match(/FlowRhythm v(\d+\.\d+\.\d+)/);
  const t = h.match(/^# (.*?) · FlowRhythm/);
  return { title: t ? t[1] : null, engine_version: v ? v[1] : null,
    historical: v ? v[1] !== ENGINE_VERSION : null };
}
