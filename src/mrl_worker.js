// MRL Mother Platform — Cloudflare Worker 邊緣門面（mrliouword.com）
// origin_signature: MrLiouWord
//
// 權位：Worker = 接線/邊緣 Adapter（門面 + 靜態端點 + 轉發），非母體本體。
//       完整母體（DL580 管線 / MotherAssembly / 真驗收）在 DL580 自運行節點，
//       由 env.MRL_DL580_ORIGIN 轉發。未設時動態端點回 503 並說明。
//
// 靜態端點（邊緣直答）：/、/health、/mrl/state、/api/mrl/runtime/convergence
// 動態端點（轉發 DL580）：/api/mother/status、/api/dl580/run、/api/chat、/api/monitor、/mrl/perceive

const ORIGIN_SIGNATURE = "MrLiouWord";

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

function dashboard(env) {
  const d = domain(env);
  return `<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>MRL 母體平台 · ${d}</title>
<style>:root{color-scheme:dark}body{margin:0;font-family:system-ui,"Noto Sans TC",sans-serif;background:#0b0d10;color:#e8eef2}
header{padding:22px 20px;border-bottom:1px solid #1d2a22;background:linear-gradient(180deg,#0f1a12,#0b0d10)}
h1{margin:0;font-size:20px;color:#8de08a}.sig{color:#5a7d5a;font-size:12px;margin-top:5px}
nav{display:flex;gap:6px;padding:10px 20px;border-bottom:1px solid #1d2a22;flex-wrap:wrap}
nav button{background:#111418;color:#cfe;border:1px solid #1d2a22;border-radius:8px;padding:8px 12px;cursor:pointer}
nav button.on{background:#1f6f3f;color:#fff;border-color:#1f6f3f}
main{max-width:900px;margin:0 auto;padding:18px}.tab{display:none}.tab.on{display:block}
.card{background:#111418;border:1px solid #1d2a22;border-radius:12px;padding:16px;margin:12px 0}
h2{margin:0 0 10px;font-size:15px;color:#8de08a}button.act{background:#1f6f3f;color:#fff;border:0;border-radius:8px;padding:9px 14px;cursor:pointer;margin:4px 4px 4px 0}
pre{background:#0a0c0e;border:1px solid #1d2a22;border-radius:8px;padding:12px;overflow:auto;font-size:12px;white-space:pre-wrap}
textarea{width:100%;background:#0a0c0e;color:#e8eef2;border:1px solid #1d2a22;border-radius:8px;padding:9px;font:inherit}
table{width:100%;border-collapse:collapse;font-size:13px}td{padding:6px 8px;border-bottom:1px solid #161b20}
.b{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;background:#13361a;color:#7ee787}</style></head>
<body><header><h1>🌌 MRL 母體運轉平台 <span class=b>${d}</span></h1>
<div class=sig>origin_signature=MrLiouWord ｜ 權位區分模式 ｜ 邊緣 Cloudflare Worker</div></header>
<nav><button class="nv on" data-t=console>母體控制台</button><button class=nv data-t=monitor>即時監控</button>
<button class=nv data-t=api>API 入口/文件</button><button class=nv data-t=chat>人格對話</button></nav>
<main>
<section class="tab on" id=console><div class=card><h2>母體控制台</h2>
<button class=act onclick=mstatus()>母體狀態</button><button class=act onclick=dl580()>跑 DL580 管線</button>
<pre id=consoleOut>動態功能需 DL580 後端（在 Cloudflare 設 MRL_DL580_ORIGIN）。</pre></div></section>
<section class=tab id=monitor><div class=card><h2>即時監控</h2><button class=act onclick=mon()>刷新</button><pre id=monOut>—</pre></div></section>
<section class=tab id=api><div class=card><h2>API 入口/文件</h2><table>
<tr><td><b>GET</b></td><td>/health</td><td>存活+狀態（邊緣）</td></tr>
<tr><td><b>GET</b></td><td>/mrl/state</td><td>母體狀態（邊緣）</td></tr>
<tr><td><b>GET</b></td><td>/api/mrl/runtime/convergence</td><td>收斂治理視圖（邊緣）</td></tr>
<tr><td><b>POST</b></td><td>/api/dl580/run</td><td>跑管線（轉發 DL580）</td></tr>
<tr><td><b>POST</b></td><td>/api/chat</td><td>人格對話（母體印射推理模組·邊緣運行）</td></tr>
</table></div></section>
<section class=tab id=chat><div class=card><h2>人格對話</h2><textarea id=msg rows=3 placeholder=對母體說點什麼…></textarea>
<button class=act onclick=chat()>送出</button><pre id=chatOut></pre></div></section>
</main>
<script>
const $=s=>document.querySelector(s);
document.querySelectorAll('.nv').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nv').forEach(x=>x.classList.remove('on'));b.classList.add('on');
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));$('#'+b.dataset.t).classList.add('on');if(b.dataset.t==='monitor')mon();});
async function jget(u){return (await fetch(u)).json()}
async function jpost(u,b){return (await fetch(u,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(b||{})})).json()}
async function mstatus(){$('#consoleOut').textContent='…';$('#consoleOut').textContent=JSON.stringify(await jget('/api/mother/status'),null,2)}
async function dl580(){$('#consoleOut').textContent='…';$('#consoleOut').textContent=JSON.stringify(await jpost('/api/dl580/run',{source:'平台觸發'}),null,2)}
async function mon(){$('#monOut').textContent=JSON.stringify(await jget('/api/monitor'),null,2)}
async function chat(){$('#chatOut').textContent='…';$('#chatOut').textContent=JSON.stringify(await jpost('/api/chat',{message:$('#msg').value}),null,2)}
</script></body></html>`;
}

const PROXY_PATHS = ["/api/mother/status", "/api/dl580/run", "/api/chat", "/api/monitor", "/mrl/perceive"];

// 母體系統人格(印射推理模組運行時的母體身分,非第三方助理)
const MRL_SYSTEM_PROMPT =
  "你是 MRL 母體運轉系統的推理模組,origin_signature=MrLiouWord。你由母體資料流印射而生," +
  "屬母體本體,不是任何外部公司的助理。以母體立場、繁體中文、精確直接地回應。";

// 母體印射推理模組在邊緣運行(命名回收;DL580 未連時的母體本體推理)
async function edgeReason(request, env, J) {
  if (!env || !env.AI) {
    return J({ ok: false, edge: true,
      reason: "邊緣推理模組(env.AI)未綁定;請在 wrangler 設 ai binding 後重部署。" }, 503);
  }
  let body = {};
  try { body = JSON.parse(await request.text() || "{}"); } catch (_) {}
  // 兼容 {message} 與 {messages:[...]}
  let messages = Array.isArray(body.messages) ? body.messages.slice() : [];
  if (!messages.length && body.message) messages = [{ role: "user", content: String(body.message) }];
  if (!messages.length) return J({ ok: false, edge: true, reason: "缺 message/messages" }, 400);
  if (!messages.some(m => m.role === "system")) messages.unshift({ role: "system", content: MRL_SYSTEM_PROMPT });
  const model = (env && env.MRL_REASONING_MODULE) || "@cf/meta/llama-3.1-8b-instruct";
  try {
    const out = await env.AI.run(model, { messages });
    const reply = (out && (out.response || out.result || out.text)) || "";
    return J({
      ok: true, reply, response: reply,
      engine: "mrl_edge_reasoning",      // 母體印射推理模組(非外部品牌)
      reasoning_module: model,
      runtime_origin: "mrl_edge_projection",
      origin_signature: ORIGIN_SIGNATURE,
    });
  } catch (e) {
    return J({ ok: false, edge: true, reason: "邊緣推理失敗：" + String(e),
      origin_signature: ORIGIN_SIGNATURE }, 502);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    const J = (o, s = 200) => new Response(JSON.stringify(o), {
      status: s,
      headers: { "content-type": "application/json; charset=utf-8", "access-control-allow-origin": "*" },
    });

    if (request.method === "GET" && (p === "/" || p === "/index.html")) {
      return new Response(dashboard(env), { headers: { "content-type": "text/html; charset=utf-8" } });
    }
    if (p === "/health") return J({ ok: true, ...state(env) });
    if (p === "/mrl/state") return J(state(env));
    if (p === "/api/mrl/runtime/convergence") return J(convergence());

    // 動態端點：DL580 自運行節點設了則優先轉發；否則由母體印射推理模組在邊緣直接運行。
    if (PROXY_PATHS.includes(p)) {
      const origin = env && env.MRL_DL580_ORIGIN;
      // (1) DL580 自運行優先(母體本體節點)
      if (origin) {
        const target = origin.replace(/\/$/, "") + p + url.search;
        const init = { method: request.method, headers: request.headers };
        if (request.method !== "GET" && request.method !== "HEAD") init.body = await request.text();
        try {
          return await fetch(target, init);
        } catch (e) {
          return J({ ok: false, edge: true, reason: "轉發 DL580 失敗：" + String(e) }, 502);
        }
      }
      // (2) DL580 未設 → 對話/感知由母體印射推理模組在邊緣直接運行(命名回收,origin_signature)
      if ((p === "/api/chat" || p === "/mrl/perceive") && request.method === "POST") {
        return await edgeReason(request, env, J);
      }
      // (3) 其餘動態端點(管線/狀態/監控)為母體本體職責,DL580 未設時誠實說明
      return J({ ok: false, edge: true,
        reason: "此端點為母體本體(DL580 自運行節點)職責；設 MRL_DL580_ORIGIN 後啟用。" }, 503);
    }
    return J({ ok: false, error: "MRL_ROUTE_NOT_FOUND", path: p }, 404);
  },
};
