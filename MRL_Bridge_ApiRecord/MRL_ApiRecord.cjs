// MRL_ApiRecord — 生產級 API 紀錄中介層（給 D:\mrl\bridge / bridge.mrliouword.com）
// origin_signature: MrLiouWord ｜ product: MrliouAI ｜ 對齊 MRL_Bridge_API v3.x
//
// 設計對齊你現行 bridge server.js：
//   - Express 風格 (res.status().json(), res.on('finish'))
//   - x-api-key 認證：req.headers['x-api-key'] || req.query.key，SHA-256 比對 apiKeyHash
//   - 落地你的 PostgreSQL（自動建表 mrl_api_records）；可選 Redis 計數
//   - 每筆蓋 origin_signature / product / trace_id / latency
//
// 上架（三行接進 bridge）：
//   const mrlApiRecord = require('./MRL_ApiRecord/MRL_ApiRecord.cjs');
//   mrlApiRecord.attach(app, { pool, redis, apiKeyHash: API_KEY_HASH });   // pool = 你的 pg Pool
//   // 完成。每個請求自動入帳；讀取端點 GET /api/mrl/records、/api/mrl/records/summary（需 x-api-key）
//
// 零新依賴：沿用 bridge 既有的 pg Pool 與 redis client（由 attach 傳入）。

'use strict';
const crypto = require('crypto');

const ORIGIN_SIGNATURE = 'MrLiouWord';
const PRODUCT = 'MrliouAI';
const SOURCE_OWNER = 'Mrliou';

let _counter = 0;
function traceId() {
  _counter = (_counter + 1) % 0xffffff;
  return `MRL-API-${Date.now().toString(36)}-${_counter.toString(16).padStart(6, '0')}`;
}

function sha256Hex(s) {
  return crypto.createHash('sha256').update(String(s)).digest('hex');
}

// 建表（冪等）。失敗不拋，只回 false，讓 bridge 照常運行。
async function ensureSchema(pool) {
  if (!pool) return false;
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS mrl_api_records (
        id            BIGSERIAL PRIMARY KEY,
        trace_id      TEXT NOT NULL,
        ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
        method        TEXT,
        path          TEXT,
        status        INTEGER,
        latency_ms    NUMERIC,
        authed        BOOLEAN,
        ip            TEXT,
        bytes         INTEGER,
        origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
        product       TEXT NOT NULL DEFAULT 'MrliouAI',
        meta          JSONB
      );
      CREATE INDEX IF NOT EXISTS idx_mrl_api_records_ts   ON mrl_api_records (ts DESC);
      CREATE INDEX IF NOT EXISTS idx_mrl_api_records_path ON mrl_api_records (path);
    `);
    return true;
  } catch (e) {
    console.error('MRL_ApiRecord ensureSchema 失敗（不中斷 bridge）:', e.message);
    return false;
  }
}

// 寫一筆紀錄。pool 失敗時退回 console（絕不中斷請求）。
async function record(pool, redis, entry) {
  const row = {
    trace_id: entry.trace_id || traceId(),
    method: entry.method || null,
    path: entry.path || null,
    status: Number.isFinite(entry.status) ? entry.status : null,
    latency_ms: Number.isFinite(entry.latency_ms) ? Number(entry.latency_ms.toFixed(2)) : null,
    authed: !!entry.authed,
    ip: entry.ip || null,
    bytes: Number.isFinite(entry.bytes) ? entry.bytes : null,
    meta: entry.meta || {},
  };
  if (redis) {
    try {
      // 輕量即時計數（best-effort）
      const p = redis.multi ? redis.multi() : null;
      if (p) {
        p.incr('mrl:api:total');
        p.incr(`mrl:api:status:${row.status}`);
        p.exec && p.exec();
      }
    } catch (e) { /* redis best-effort */ }
  }
  if (pool) {
    try {
      await pool.query(
        `INSERT INTO mrl_api_records
           (trace_id, method, path, status, latency_ms, authed, ip, bytes, origin_signature, product, meta)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)`,
        [row.trace_id, row.method, row.path, row.status, row.latency_ms, row.authed,
         row.ip, row.bytes, ORIGIN_SIGNATURE, PRODUCT, JSON.stringify(row.meta)]
      );
      return row;
    } catch (e) {
      console.error('MRL_ApiRecord record 失敗（不中斷）:', e.message);
    }
  } else {
    console.log('MRL_ApiRecord', row.trace_id, JSON.stringify(row));
  }
  return row;
}

// x-api-key 認證（對齊 bridge：header x-api-key 或 ?key=；SHA-256 比對）。
function checkAuth(req, apiKeyHash) {
  if (!apiKeyHash) return true; // 未提供 hash → 不強制（維運可先關）
  const key = (req.headers && req.headers['x-api-key']) || (req.query && req.query.key);
  if (!key) return false;
  return sha256Hex(key) === apiKeyHash;
}

// Express middleware：對每個請求在回應結束時入帳。
function middleware(opts) {
  const { pool, redis, apiKeyHash } = opts || {};
  return function mrlApiRecordMw(req, res, next) {
    const t0 = process.hrtime.bigint();
    let nbytes = 0;
    const _write = res.write, _end = res.end;
    res.write = function (chunk, ...a) { if (chunk) nbytes += chunk.length; return _write.call(this, chunk, ...a); };
    res.end = function (chunk, ...a) { if (chunk) nbytes += chunk.length; return _end.call(this, chunk, ...a); };
    res.on('finish', () => {
      const latency_ms = Number(process.hrtime.bigint() - t0) / 1e6;
      record(pool, redis, {
        method: req.method,
        path: (req.originalUrl || req.url || '').split('?')[0],
        status: res.statusCode,
        latency_ms,
        authed: checkAuth(req, apiKeyHash),
        ip: (req.headers && (req.headers['x-forwarded-for'] || req.headers['cf-connecting-ip'])) ||
            (req.socket && req.socket.remoteAddress) || null,
        bytes: nbytes,
        meta: { ua: req.headers && req.headers['user-agent'] },
      });
    });
    if (typeof next === 'function') next();
  };
}

// 讀取端點：GET /api/mrl/records（最近 n 筆）、GET /api/mrl/records/summary（聚合）。
function mountRoutes(app, opts) {
  const { pool, apiKeyHash } = opts || {};
  const guard = (req, res) => {
    if (!checkAuth(req, apiKeyHash)) {
      res.status(401).json({ ok: false, origin_signature: ORIGIN_SIGNATURE,
        error: 'API key required. Header: x-api-key or query: ?key=YOUR_KEY' });
      return false;
    }
    return true;
  };
  app.get('/api/mrl/records', async (req, res) => {
    if (!guard(req, res)) return;
    const n = Math.min(500, Math.max(1, parseInt((req.query && req.query.n) || '50', 10) || 50));
    try {
      const r = await pool.query(
        'SELECT trace_id, ts, method, path, status, latency_ms, authed, ip, bytes, meta FROM mrl_api_records ORDER BY id DESC LIMIT $1', [n]);
      res.status(200).json({ ok: true, origin_signature: ORIGIN_SIGNATURE, product: PRODUCT,
        count: r.rows.length, records: r.rows });
    } catch (e) {
      res.status(500).json({ ok: false, origin_signature: ORIGIN_SIGNATURE, error: e.message });
    }
  });
  app.get('/api/mrl/records/summary', async (req, res) => {
    if (!guard(req, res)) return;
    try {
      const total = await pool.query('SELECT count(*)::int AS c FROM mrl_api_records');
      const byPath = await pool.query('SELECT path, count(*)::int AS c FROM mrl_api_records GROUP BY path ORDER BY c DESC LIMIT 50');
      const byStatus = await pool.query('SELECT status, count(*)::int AS c FROM mrl_api_records GROUP BY status ORDER BY c DESC');
      res.status(200).json({ ok: true, origin_signature: ORIGIN_SIGNATURE, product: PRODUCT,
        total: total.rows[0].c,
        by_path: Object.fromEntries(byPath.rows.map(r => [r.path, r.c])),
        by_status: Object.fromEntries(byStatus.rows.map(r => [String(r.status), r.c])) });
    } catch (e) {
      res.status(500).json({ ok: false, origin_signature: ORIGIN_SIGNATURE, error: e.message });
    }
  });
}

// 一鍵接入：建表 + middleware + 讀取端點。
function attach(app, opts) {
  const o = opts || {};
  if (o.pool) ensureSchema(o.pool); // async，不阻塞
  app.use(middleware(o));
  mountRoutes(app, o);
  console.log(`MRL_ApiRecord attached — origin_signature=${ORIGIN_SIGNATURE}, pg=${!!o.pool}, redis=${!!o.redis}`);
  return app;
}

module.exports = { attach, middleware, mountRoutes, record, ensureSchema, checkAuth, traceId,
  ORIGIN_SIGNATURE, PRODUCT, SOURCE_OWNER };
