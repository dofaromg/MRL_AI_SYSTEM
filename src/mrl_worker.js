// MRL Mother Platform — Cloudflare Worker 邊緣門面（mrliouword.com）
// origin_signature: MrLiouWord
//
// 權位：Worker = 接線/邊緣 Adapter（門面 + 靜態端點 + 轉發），非母體本體。
//       完整母體（DL580 管線 / MotherAssembly / 真驗收）在 DL580 自運行節點，
//       由 env.MRL_DL580_ORIGIN 轉發。未設時動態端點回 503 並說明。
//
// 靜態端點（邊緣直答）：/、/health、/mrl/state、/api/mrl/runtime/convergence
// 動態端點（轉發 DL580）：/api/mother/status、/api/dl580/run、/api/chat、/api/monitor、/mrl/perceive
// 除錯收集端點（邊緣直答）：POST /__manus__/logs — 前端內嵌除錯收集器上報 console/network/ui 事件

import { APP_HTML } from "./mrl_app_ui.js";

const ORIGIN_SIGNATURE = "MrLiouWord";

// CORS：允許前端跨域上報（含 POST JSON 前的 preflight 預檢）。
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

// MRL 結構化封裝：把前端內嵌收集器上報的除錯日誌收斂成母體標準封包，
// 蓋 origin_signature 追蹤標記與唯一識別 (trace_id)，欄位缺漏一律歸零陣列以保安全。
function wrapManusLogs(payload, request) {
  const safe = (payload && typeof payload === "object") ? payload : {};
  const asArray = (v) => (Array.isArray(v) ? v : []);
  const consoleLogs = asArray(safe.consoleLogs);
  const networkRequests = asArray(safe.networkRequests);
  const uiEvents = asArray(safe.uiEvents);
  return {
    origin_signature: ORIGIN_SIGNATURE,
    mrl_kind: "MRL_ManusDebugLogPacket",
    trace_id: mrlTraceId(),
    received_at: new Date().toISOString(),
    source: {
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

// 唯一識別（防碰撞）：時間前綴保留粗略可排序性；crypto.randomUUID() 提供隨機性，
// 避免同毫秒併發的兩個請求拿到相同 trace_id。極端環境無 randomUUID 時退回隨機後備。
function mrlTraceId() {
  const t = Date.now().toString(36);
  let rand;
  try {
    rand = crypto.randomUUID();
  } catch (e) {
    rand = t + "-" + Math.random().toString(36).slice(2, 14);
  }
  return "MRL-MANUS-" + t + "-" + rand;
}

// 上限守則：公開端點須有邊界。
const MAX_BODY_BYTES = 256 * 1024; // 256KB：debug 日誌批次的合理上限，逾者回 413。
const MAX_LOG_CHARS = 20000;       // 單筆 observability log 的截斷上限，避免整筆遺失。

// 將 MRL 封包（含 payload）寫入邊緣可觀測性日誌（wrangler.jsonc observability.enabled=true 會收集）；
// 確保 console/network/ui 內容真正落地，而非只留計數。逾量截斷但保留 counts 與前段內容。
function emitPacketLog(packet) {
  let serialized;
  try {
    serialized = JSON.stringify(packet);
  } catch (e) {
    serialized = JSON.stringify({ trace_id: packet.trace_id, counts: packet.counts, serialize_error: String(e) });
  }
  if (serialized.length > MAX_LOG_CHARS) {
    console.log("MRL_ManusDebugLogPacket", packet.trace_id, "TRUNCATED",
      JSON.stringify(packet.counts), serialized.slice(0, MAX_LOG_CHARS));
  } else {
    console.log("MRL_ManusDebugLogPacket", packet.trace_id, serialized);
  }
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

    // CORS 預檢：邊緣統一處理所有路徑的 OPTIONS preflight（含代理 /api/*），一律回
    // 204 + CORS，使前端跨域 POST 不被阻擋。此為刻意的邊緣層行為（非只限
    // /__manus__/logs）；代理端點的實際（非 OPTIONS）請求仍照常轉發 DL580。
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    // 除錯收集端點：前端內嵌收集器 POST /__manus__/logs 上報 console/network/ui 事件。
    // 大小防護 → 安全 await request.json() 解析 → MRL 母體結構化封裝 → 收斂 observability → 回 200。
    if (p === "/__manus__/logs" && request.method === "POST") {
      // 大小防護：公開端點（allow-origin:*）先以 content-length 粗略擋超大 body，
      // 避免 await request.json() 把過大內容讀進記憶體造成 CPU/記憶體壓力。
      const declaredLen = Number(request.headers.get("content-length") || 0);
      if (Number.isFinite(declaredLen) && declaredLen > MAX_BODY_BYTES) {
        return J({ success: false, origin: ORIGIN_SIGNATURE, error: "MRL_PAYLOAD_TOO_LARGE", max_bytes: MAX_BODY_BYTES }, 413);
      }
      let body;
      try {
        body = await request.json();
      } catch (e) {
        // 內容非合法 JSON：誠實回 400（不謊報 success），仍附 CORS 讓前端能讀到回應。
        return J({ success: false, origin: ORIGIN_SIGNATURE, error: "MRL_INVALID_JSON" }, 400);
      }
      const packet = wrapManusLogs(body, request);
      // 收斂完整封包（含 payload）到 observability，而非只留計數；逾量截斷。
      emitPacketLog(packet);
      return J({ success: true, origin: ORIGIN_SIGNATURE });
    }

    if (request.method === "GET" && (p === "/" || p === "/index.html")) {
      return new Response(dashboard(env), { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (p === "/health") return J({ ok: true, ...state(env) });
    if (p === "/mrl/state") return J(state(env));
    if (p === "/api/mrl/runtime/convergence") return J(convergence());

    // 動態端點 → 轉發 DL580 母體後端
    if (PROXY_PATHS.includes(p)) {
      const origin = env && env.MRL_DL580_ORIGIN;
      if (!origin) {
        return J({ ok: false, edge: true,
          reason: "DL580 後端未設定。請在 Cloudflare 變數設 MRL_DL580_ORIGIN=https://<DL580 對外網址>；此端點需母體後端（Python 不在邊緣執行）。" }, 503);
      }
      const target = origin.replace(/\/$/, "") + p + url.search;
      const init = { method: request.method, headers: request.headers };
      if (request.method !== "GET" && request.method !== "HEAD") init.body = await request.text();
      try {
        return await fetch(target, init);
      } catch (e) {
        return J({ ok: false, edge: true, reason: "轉發 DL580 失敗：" + String(e) }, 502);
      }
    }
    return J({ ok: false, error: "MRL_ROUTE_NOT_FOUND", path: p }, 404);
  },
};
