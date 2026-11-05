// 用 mock Express + mock pg 驗證 MRL_ApiRecord.cjs 的邏輯（無需真 pg/express）。
const EventEmitter = require('node:events');
const mod = require('./MRL_ApiRecord.cjs');
const crypto = require('crypto');

let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log('  PASS ', m); } else { fail++; console.log('  FAIL ', m); } };

// ── mock pg pool ──
const inserts = [];
const pool = {
  async query(sql, params) {
    if (/INSERT INTO mrl_api_records/.test(sql)) { inserts.push(params); return { rows: [] }; }
    if (/CREATE TABLE/.test(sql)) return { rows: [] };
    if (/SELECT .* FROM mrl_api_records ORDER BY/.test(sql)) return { rows: inserts.map((p, i) => ({ trace_id: p[0], method: p[1], path: p[2], status: p[3] })).slice(0, params[0]) };
    if (/count\(\*\)::int AS c FROM mrl_api_records$/.test(sql)) return { rows: [{ c: inserts.length }] };
    if (/GROUP BY path/.test(sql)) return { rows: [{ path: '/health', c: 2 }] };
    if (/GROUP BY status/.test(sql)) return { rows: [{ status: 200, c: 2 }] };
    return { rows: [] };
  },
};

// ── mock express app ──
const routes = {};
const app = { _mw: [], use(fn) { this._mw.push(fn); }, get(p, fn) { routes['GET ' + p] = fn; } };

const API_KEY = 'MrLiouWord2026';
const API_KEY_HASH = crypto.createHash('sha256').update(API_KEY).digest('hex');

(async () => {
  mod.attach(app, { pool, redis: null, apiKeyHash: API_KEY_HASH });
  ok(app._mw.length === 1, 'middleware 已掛載');
  ok(!!routes['GET /api/mrl/records'] && !!routes['GET /api/mrl/records/summary'], '讀取端點已註冊');

  // 模擬一個請求走完 middleware → finish → 入帳
  function fakeReqRes(method, url, headers = {}) {
    const req = { method, url, originalUrl: url, headers, query: {}, socket: { remoteAddress: '1.2.3.4' } };
    const res = new EventEmitter();
    res.statusCode = 200;
    res.write = () => true; res.end = () => { res.emit('finish'); };
    return { req, res };
  }
  const mw = app._mw[0];
  await new Promise((resolve) => {
    const { req, res } = fakeReqRes('GET', '/health');
    mw(req, res, () => {});
    res.end(Buffer.from('{"ok":true}'));
    setTimeout(resolve, 20); // 等 finish handler 的 async record
  });
  await new Promise((r) => setTimeout(r, 20));
  ok(inserts.length === 1, '請求結束後入帳一筆');
  ok(inserts[0][2] === '/health' && inserts[0][3] === 200, '入帳 path=/health status=200');
  ok(inserts[0][8] === 'MrLiouWord', '入帳蓋 origin_signature=MrLiouWord');

  // 讀取端點：未帶 key → 401
  let out = null;
  const res401 = { status(c) { this._c = c; return this; }, json(o) { out = { c: this._c, o }; } };
  await routes['GET /api/mrl/records']({ headers: {}, query: {} }, res401);
  ok(out.c === 401 && /API key required/.test(out.o.error), '無 x-api-key → 401');

  // 帶正確 key → 200 + records
  let out2 = null;
  const res200 = { status(c) { this._c = c; return this; }, json(o) { out2 = { c: this._c, o }; } };
  await routes['GET /api/mrl/records']({ headers: { 'x-api-key': API_KEY }, query: { n: '10' } }, res200);
  ok(out2.c === 200 && out2.o.ok === true && out2.o.origin_signature === 'MrLiouWord', '正確 key → 200 records');

  // summary
  let out3 = null;
  const res3 = { status(c) { this._c = c; return this; }, json(o) { out3 = { c: this._c, o }; } };
  await routes['GET /api/mrl/records/summary']({ headers: { 'x-api-key': API_KEY }, query: {} }, res3);
  ok(out3.c === 200 && out3.o.total === 1 && out3.o.by_status['200'] === 2, 'summary 聚合正確');

  // auth helper 直接測
  ok(mod.checkAuth({ headers: { 'x-api-key': API_KEY } }, API_KEY_HASH) === true, 'checkAuth 正確 key 通過');
  ok(mod.checkAuth({ headers: { 'x-api-key': 'wrong' } }, API_KEY_HASH) === false, 'checkAuth 錯 key 擋下');
  ok(mod.traceId().startsWith('MRL-API-'), 'traceId 前綴正確');

  console.log(`\n=== ${pass} passed, ${fail} failed ===`);
  process.exit(fail === 0 ? 0 : 1);
})();
