// MRL Mother Platform — Cloudflare Worker 邊緣門面（mrliouword.com）
// origin_signature: MrLiouWord
//
// 權位：Worker = 接線/邊緣 Adapter（門面 + 靜態端點 + 轉發），非母體本體。
//       完整母體（DL580 管線 / MotherAssembly / 真驗收）在 DL580 自運行節點，
//       由 env.MRL_DL580_ORIGIN 轉發。未設時動態端點回 503 並說明。
//
// 靜態端點（邊緣直答）：/、/health、/mrl/state、/api/mrl/runtime/convergence
// 動態端點（轉發 DL580）：/api/mother/status、/api/dl580/run、/api/chat、/api/monitor、/mrl/perceive
// 產品遙測端點（邊緣直答）：POST /api/mrl/telemetry/logs — Mrliou 產品前端上報 console/network/ui 事件
// 語場節奏（邊緣直答）：POST /api/rhythm/run、/api/rhythm/replay — FlowRhythm v0.2.0，?sandbox=1 才允許 provisional

import { APP_HTML } from "./mrl_app_ui.js";
import { legacyDashboard } from "./mrl_dashboard_legacy.js";

// FlowRhythm v0 邊緣載體（Jump → Collapse → Trace → Replay），與本體 flow_rhythm.py v0.2.0 逐位元組一致
// 驗收：node MRL_WorldModel/MRL_FlowRhythm_v0/edge/conformance.mjs
import * as Rhythm from "../MRL_WorldModel/MRL_FlowRhythm_v0/edge/flow_rhythm.mjs";
import RHYTHM_LEXICON from "../MRL_WorldModel/MRL_FlowRhythm_v0/edge/lexicon.v0.2.0.json";
let _rhythmLex = null;
const rhythmLex = () => (_rhythmLex ||= Rhythm.prepareLexicon(RHYTHM_LEXICON));

const ORIGIN_SIGNATURE = "MrLiouWord";
const PRODUCT_NAME = "MrliouAI";
const SOURCE_OWNER = "Mrliou";

// CORS：允許產品前端跨域上報（含 POST JSON 前的 preflight 預檢）。
// x-mrl-origin-signature 為 MRL 母體追蹤標記，蓋在每個 JSON 回應上。
const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type, x-mrl-origin-signature",
  "access-control-max-age": "86400",
};

function domain(env) {
  return (env && env.MRL_PLATFORM_DOMAIN) || "mrliouword.com";
}

function state(env) {
  return {
    origin_signature: ORIGIN_SIGNATURE,
    product: PRODUCT_NAME,
    source_owner: SOURCE_OWNER,
    system_name: "MRL_完整態母體運轉系統_v1",
    platform: domain(env),
    edge: "Cloudflare Worker (接線/Adapter)",
    sovereignty_mode: "權位區分模式",
    status: "running",
    attention_policy: "Attention 為歷史層；正式主體為感知力(Perception)",
  };
}

function convergence() {
  return {
    status: "SPEC_READY", implementation: "READ_ONLY_API_ACTIVE",
    active: { runtime_core: "LOCAL_ACCEPTANCE", naming_alignment: "LOCAL_ACCEPTANCE",
      pid_scope: "DECLARED_ACTIVE", entry_gateway: "DECLARED_ACTIVE" },
    pending: { persistent_loop_daemon: "PENDING", replay_restore_runtime: "PENDING",
      world_sync: "PENDING", baseworld_db: "PENDING", dl580_reboot_survival: "PENDING" },
    note: "唯讀治理視圖；不啟動 daemon、不宣稱 pending 完成。",
  };
}

// 產品級入口 (MRL_Product_Entry_UI · Issue #25/#26/#27/#28/#29)。
// HTML 單一來源 = src/mrl_app.html，由 scripts/MRL_build_ui.js 產生 mrl_app_ui.js。
// 動態 /api/* 由下方 PROXY_PATHS 轉發 DL580；未設時前端誠實顯示「需母體後端」。
function dashboard(env) {
  return APP_HTML;
}

// MRL 結構化封裝：把 Mrliou 產品前端上報的除錯日誌收斂成母體標準封包。
// 產品、來源主體與 provenance 分欄記錄，禁止把外部平台名稱升格為 canonical 主體。
function wrapMRLDebugLogs(payload, request) {
  const safe = (payload && typeof payload === "object") ? payload : {};
  const asArray = (v) => (Array.isArray(v) ? v : []);
  const consoleLogs = asArray(safe.consoleLogs);
  const networkRequests = asArray(safe.networkRequests);
  const uiEvents = asArray(safe.uiEvents);
  return {
    product: PRODUCT_NAME,
    source_owner: SOURCE_OWNER,
    origin_signature: ORIGIN_SIGNATURE,
    mrl_kind: "MRL_DebugLogPacket",
    trace_id: mrlTraceId(),
    received_at: new Date().toISOString(),
    source: {
      owner: SOURCE_OWNER,
      product: PRODUCT_NAME,
      referer: (request && request.headers.get("referer")) || null,
      user_agent: (request && request.headers.get("user-agent")) || null,
    },
    counts: {
      consoleLogs: consoleLogs.length,
      networkRequests: networkRequests.length,
      uiEvents: uiEvents.length,
    },
    payload: { consoleLogs, networkRequests, uiEvents },
  };
}

// 唯一識別（防碰撞）：時間前綴保留粗略可排序性；crypto.randomUUID() 提供隨機性。
function mrlTraceId() {
  const t = Date.now().toString(36);
  let rand;
  try {
    rand = crypto.randomUUID();
  } catch (e) {
    rand = t + "-" + Math.random().toString(36).slice(2, 14);
  }
  return "MRL-DEBUG-" + t + "-" + rand;
}

// 上限守則：公開端點須有邊界。
const MAX_BODY_BYTES = 256 * 1024;
const MAX_LOG_CHARS = 20000;

// 將 MRL 封包（含 payload）寫入邊緣可觀測性日誌；逾量截斷但保留 counts 與前段內容。
function emitPacketLog(packet) {
  let serialized;
  try {
    serialized = JSON.stringify(packet);
  } catch (e) {
    serialized = JSON.stringify({ trace_id: packet.trace_id, counts: packet.counts, serialize_error: String(e) });
  }
  if (serialized.length > MAX_LOG_CHARS) {
    console.log("MRL_DebugLogPacket", packet.trace_id, "TRUNCATED",
      JSON.stringify(packet.counts), serialized.slice(0, MAX_LOG_CHARS));
  } else {
    console.log("MRL_DebugLogPacket", packet.trace_id, serialized);
  }
}

async function readBoundedBody(request) {
  const reader = request.body?.getReader();
  const chunks = [];
  let totalBytes = 0;

  if (reader) {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        totalBytes += value.byteLength;
        if (totalBytes > MAX_BODY_BYTES) {
          try {
            await reader.cancel();
          } catch (e) {
            // The request may already have been cancelled by the runtime.
          }
          return null;
        }
        chunks.push(value);
      }
    } finally {
      reader.releaseLock();
    }
  }

  const body = new Uint8Array(totalBytes);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

// 常數時間比對（以 SHA-256 摘要比較，避免長度與逐字元時間差洩漏）
async function sameSecret(a, b) {
  if (!a || !b) return false;
  const enc = new TextEncoder();
  const [x, y] = await Promise.all([crypto.subtle.digest("SHA-256", enc.encode(a)), crypto.subtle.digest("SHA-256", enc.encode(b))]);
  const u = new Uint8Array(x), v = new Uint8Array(y);
  let d = 0; for (let i = 0; i < u.length; i++) d |= u[i] ^ v[i];
  return d === 0;
}

const PROXY_PATHS = ["/api/mother/status", "/api/dl580/run", "/api/chat", "/api/monitor", "/mrl/perceive"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    const J = (o, s = 200) => new Response(JSON.stringify(o), {
      status: s,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "x-mrl-origin-signature": ORIGIN_SIGNATURE,
        ...CORS_HEADERS,
      },
    });

    // CORS 預檢：邊緣統一處理所有路徑的 OPTIONS preflight（含代理 /api/*）。
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // Mrliou 產品遙測端點：POST /api/mrl/telemetry/logs。
    if (p === "/api/mrl/telemetry/logs" && request.method === "POST") {
      const declaredLen = Number(request.headers.get("content-length") || 0);
      if (Number.isFinite(declaredLen) && declaredLen > MAX_BODY_BYTES) {
        return J({
          success: false,
          product: PRODUCT_NAME,
          source_owner: SOURCE_OWNER,
          error: "MRL_PAYLOAD_TOO_LARGE",
          max_bytes: MAX_BODY_BYTES,
        }, 413);
      }
      let body;
      try {
        const bodyBytes = await readBoundedBody(request);
        if (bodyBytes === null) {
          return J({
            success: false,
            product: PRODUCT_NAME,
            source_owner: SOURCE_OWNER,
            error: "MRL_PAYLOAD_TOO_LARGE",
            max_bytes: MAX_BODY_BYTES,
          }, 413);
        }
        body = JSON.parse(new TextDecoder().decode(bodyBytes));
      } catch (e) {
        return J({
          success: false,
          product: PRODUCT_NAME,
          source_owner: SOURCE_OWNER,
          error: "MRL_INVALID_JSON",
        }, 400);
      }
      const packet = wrapMRLDebugLogs(body, request);
      emitPacketLog(packet);
      return J({
        success: true,
        product: PRODUCT_NAME,
        source_owner: SOURCE_OWNER,
        origin_signature: ORIGIN_SIGNATURE,
      });
    }

    if (request.method === "GET" && (p === "/" || p === "/index.html")) {
      return new Response(dashboard(env), { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (request.method === "GET" && p === "/console/legacy") {
      return new Response(legacyDashboard(env), { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (p === "/health") return J({ ok: true, ...state(env) });
    if (p === "/mrl/state") return J(state(env));
    if (p === "/api/mrl/runtime/convergence") return J(convergence());

    // FlowRhythm：POST 純文字。預設正典 fail-closed；?sandbox=1 才允許 PROVISIONAL_NOT_CANONICAL（輸出永久標記）
    if (p === "/api/rhythm/replay" || p === "/api/rhythm/run") {
      if (request.method !== "POST") return J({ ok: false, error: "POST text/plain" }, 405);
      const text = await request.text();
      const allowProvisional = url.searchParams.get("sandbox") === "1";
      const title = url.searchParams.get("title") || "語場節奏";
      try {
        const L = rhythmLex();
        const r = p.endsWith("/replay")
          ? await Rhythm.replay(text, L, { title, allowProvisional })
          : await Rhythm.run(Rhythm.chainFromFltnz(text), L, { title, allowProvisional });
        return J({ ok: true, carrier: "edge", engine_version: Rhythm.ENGINE_VERSION,
          semantic_status: r.semantic_status, provisional_mappings: r.provisional_mappings,
          final_sha256: r.final_sha256, byte_identical: r.byte_identical, trace_ops: r.trace_ops,
          chain: r.chain, packets: r.field.packets, trace_fltnz: r.trace_fltnz, narration: r.narration,
          header: Rhythm.traceHeaderInfo(r.trace_fltnz) });
      } catch (e) {
        return J({ ok: false, error: e.name, reason: e.message,
          header: p.endsWith("/replay") ? Rhythm.traceHeaderInfo(text) : undefined }, 422);
      }
    }

    // 動態端點 → 轉發 DL580 母體後端
    if (PROXY_PATHS.includes(p)) {
      // 奇異點優先（2026-10-03）：MRL_DL580_ORIGIN = 固定 IP 入口（origin.mrliouword.com → 220.132.58.129），
      // 失敗時依序試 MRL_DL580_ORIGIN_FALLBACK（逗號分隔，例：Tunnel 入口 https://dl580.mrliouword.com）。
      // 兩個入口皆由 Cloudflare Access 保護；Worker 以 secret MRL_DL580_ACCESS_ID／SECRET 帶 service token。
      const origins = [env && env.MRL_DL580_ORIGIN, ...String((env && env.MRL_DL580_ORIGIN_FALLBACK) || "").split(",")]
        .map((o) => (o || "").trim()).filter(Boolean);
      if (!origins.length) {
        return J({ ok: false, edge: true,
          reason: "DL580 後端未設定。請在 Cloudflare 變數設 MRL_DL580_ORIGIN=https://<DL580 對外網址>；此端點需母體後端（Python 不在邊緣執行）。" }, 503);
      }
      // 呼叫端授權（Codex P1 修補）：Access service token 只代表 Worker，不代表呼叫者。
      // 呼叫者須帶 x-mrl-edge-token（或 Authorization: Bearer）= secret MRL_EDGE_TOKEN；未設 secret 一律拒絕（fail-closed）。
      const presented = request.headers.get("x-mrl-edge-token")
        || (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
      if (!env.MRL_EDGE_TOKEN || !(await sameSecret(presented, env.MRL_EDGE_TOKEN))) {
        return J({ ok: false, edge: true, error: "MRL_EDGE_UNAUTHORIZED",
          reason: "此端點會操作 DL580 母體，需呼叫端授權（x-mrl-edge-token）。" }, 401);
      }
      const headers = new Headers(request.headers);
      headers.delete("cf-access-client-id"); headers.delete("cf-access-client-secret"); headers.delete("cookie");
      headers.delete("x-mrl-edge-token"); headers.delete("authorization");
      if (env.MRL_DL580_ACCESS_ID && env.MRL_DL580_ACCESS_SECRET) {
        headers.set("CF-Access-Client-Id", env.MRL_DL580_ACCESS_ID);
        headers.set("CF-Access-Client-Secret", env.MRL_DL580_ACCESS_SECRET);
      }
      const body = (request.method !== "GET" && request.method !== "HEAD") ? await request.text() : undefined;
      const idempotent = request.method === "GET" || request.method === "HEAD";
      const tried = [];
      for (const origin of origins) {
        const host = origin.replace(/^https?:\/\//, "").replace(/\/.*$/, "");
        try {
          const r = await fetch(origin.replace(/\/$/, "") + p + url.search, { method: request.method, headers, body, redirect: "manual" });
          // 換下一個入口的條件（Codex P1 修補：非冪等請求不得重送）：
          //   請求確定未到達 DL580（連不上、TLS 失敗、Tunnel 斷、Access 擋下）→ 任何方法都可換入口；
          //   520／524（可能已到達、執行中逾時）→ 只有 GET／HEAD 可換入口，POST 照實回報，不重送。
          const neverReached = [521, 522, 523, 525, 526, 530, 301, 302, 401, 403].includes(r.status);
          const ambiguous = [520, 524].includes(r.status);
          if (neverReached || (ambiguous && idempotent)) {
            tried.push({ entry: host, status: r.status }); continue;
          }
          const out = new Response(r.body, r);
          out.headers.set("x-mrl-dl580-entry", host);
          return out;
        } catch (e) {
          tried.push({ entry: host, error: String(e) });
          if (!idempotent) break;   // 例外時無法確定是否已送達 → 非冪等請求不重送
        }
      }
      return J({ ok: false, edge: true, reason: "DL580 各入口皆未接通（不代表 DL580 離線，僅代表這些路徑不通）", tried }, 502);
    }
    return J({ ok: false, error: "MRL_ROUTE_NOT_FOUND", path: p }, 404);
  },
};
