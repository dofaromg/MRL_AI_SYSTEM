// 舊版邊緣控制台（mrl-mother-platform 原 dashboard），整合後保留於 /console/legacy，不刪除
// origin_signature: MrLiouWord ｜ Additive-Only

function domain(env) {
  return (env && env.MRL_PLATFORM_DOMAIN) || "mrliouword.com";
}

export function legacyDashboard(env) {
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
<tr><td><b>POST</b></td><td>/api/chat</td><td>人格對話（轉發 DL580）</td></tr>
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
