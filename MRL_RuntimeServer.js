const http = require('http');
const runtime = require('./MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_API/MRL_RuntimeServer');
const manifest = require('./data/MRL_runtime_gateway_manifest.json');

const {
  convergence_view: MRL_CONVERGENCE_VIEW,
  perception: MRL_PERCEPTION,
  ...MRL_STATE
} = manifest;

const runtimeHandler = runtime.server.listeners('request')[0];

function sendJSON(res, code, obj) {
  res.writeHead(code, { 'content-type': 'application/json' });
  res.end(JSON.stringify(obj));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    let settled = false;
    const fail = err => { if (settled) return; settled = true; reject(err); };
    req.on('data', chunk => {
      if (settled) return;
      data += chunk;
      if (data.length > runtime.MRL_CFG.max_body_bytes) {
        const err = new Error('MRL_BODY_TOO_LARGE');
        err.code = 413;
        fail(err);
        req.destroy();
      }
    });
    req.on('end', () => {
      if (settled) return;
      settled = true;
      try { resolve(data ? JSON.parse(data) : {}); } catch (e) { reject(e); }
    });
    req.on('error', fail);
  });
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/health') {
      return sendJSON(res, 200, { ok: true, ...MRL_STATE });
    }
    if (req.method === 'GET' && req.url === '/mrl/state') {
      return sendJSON(res, 200, MRL_STATE);
    }
    if (req.method === 'GET' && req.url === '/api/mrl/runtime/convergence') {
      return sendJSON(res, 200, MRL_CONVERGENCE_VIEW);
    }
    if (req.method === 'POST' && req.url === '/mrl/perceive') {
      const input = await readBody(req);
      return sendJSON(res, 200, {
        ok: true,
        route: MRL_PERCEPTION.route,
        input,
        flow: MRL_PERCEPTION.flow,
        sovereignty: MRL_PERCEPTION.sovereignty
      });
    }
    return runtimeHandler(req, res);
  } catch (e) {
    return sendJSON(res, e.code || 500, { error: 'MRL_GATEWAY_ERROR', message: e.message });
  }
});

if (require.main === module) {
  const port = Number(process.env.MRL_PORT || 8790);
  const host = process.env.MRL_HOST || '0.0.0.0';
  server.listen(port, host, () => {
    console.log(`MRL Runtime Gateway running at http://${host}:${port}`);
  });
}

module.exports = { ...runtime, server };
