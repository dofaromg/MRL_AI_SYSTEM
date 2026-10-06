// origin_signature: MrLiouWord
// node --test MRL_WorldModel/MRL_FlowRhythm_v0/edge/MRL_fail_closed.test.mjs
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { registerHooks } from 'node:module';
import * as R from './flow_rhythm.mjs';

// Node requires a JSON import attribute; Workers accepts this existing import.
registerHooks({ load(url, context, nextLoad) {
  if (url.endsWith('/lexicon.v0.2.0.json')) return {
    format: 'module', source: `export default ${readFileSync(new URL(url), 'utf8')}`, shortCircuit: true,
  };
  return nextLoad(url, context);
}});
const { default: worker } = await import('../../../src/mrl_worker.js');
const L = R.prepareLexicon(JSON.parse(readFileSync(new URL('./lexicon.v0.2.0.json', import.meta.url))));
const fixed = '2025-07-23T19:41:36.746707Z';
const python = (input) => JSON.parse(execFileSync('python3', ['-c', `
import json,sys
sys.path.insert(0,sys.argv[1])
import flow_rhythm as F
x=json.load(sys.stdin); L=F.load_lexicon()
try:
 if x.get('trace') is not None:
  r=F.replay(x['trace'],L,title=x['title'],allow_provisional=x['sandbox'])
 else:
  r=F.run(x['chain'],L,F.Clock('${fixed}'),x['title'],allow_provisional=x['sandbox'])
 print(json.dumps({'trace':r['trace_fltnz'],'hash':r['final_sha256']}))
except F.SemanticAuthorityIntegrityError as e:
 print(json.dumps({'error':type(e).__name__}))
`, new URL('../', import.meta.url).pathname], { input: JSON.stringify(input), encoding: 'utf8' }));

for (const token of ['⋄fx.time.010', '⋄fx.gate.001', '⋄fx.per.001']) {
  for (const sandbox of [false, true]) test(`unmapped ${token}, sandbox=${sandbox}`, async () => {
    const opts = { title: 'MRL', allowProvisional: sandbox };
    await assert.rejects(R.run([token], L, opts), R.SemanticAuthorityIntegrityError);
    assert.equal(python({ chain: [token], title: 'MRL', sandbox }).error, 'SemanticAuthorityIntegrityError');
    const base = await R.run(['⊕:MRL'], L, { title: 'MRL' });
    const forged = base.trace_fltnz.replace('→ ⊕:MRL', `→ ${token}`);
    await assert.rejects(R.replay(forged, L, opts), R.SemanticAuthorityIntegrityError);
    assert.equal(python({ trace: forged, title: 'MRL', sandbox }).error, 'SemanticAuthorityIntegrityError');
  });
}
for (const title of ['\n', '\r', '\r\n', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029'].map(sep => `MRL${sep}break`)) test(`reject title ${JSON.stringify(title)}`, async () => {
  for (const sandbox of [false, true]) {
    const opts = { title, allowProvisional: sandbox };
    await assert.rejects(R.run(['⊕:MRL'], L, opts), R.SemanticAuthorityIntegrityError);
    assert.equal(python({ chain: ['⊕:MRL'], title, sandbox }).error, 'SemanticAuthorityIntegrityError');
    const base = await R.run(['⊕:MRL'], L);
    await assert.rejects(R.replay(base.trace_fltnz, L, opts), R.SemanticAuthorityIntegrityError);
    assert.equal(python({ trace: base.trace_fltnz, title, sandbox }).error, 'SemanticAuthorityIntegrityError');
  }
});
test('valid Unicode title preserves JS/Python run and bidirectional replay', async () => {
  const title = 'MRL 語場 🌀';
  const chain = ['⊕:MRL'];
  const js = await R.run(chain, L, { title, clock: new R.Clock({ fixed }) });
  const py = python({ chain, title, sandbox: false });
  assert.equal(js.trace_fltnz, py.trace); assert.equal(js.final_sha256, py.hash);
  assert.equal((await R.replay(py.trace, L, { title })).byte_identical, true);
  assert.deepEqual(python({ trace: js.trace_fltnz, title, sandbox: false }), py);
});

const limit = 256 * 1024;
const enc = new TextEncoder();
async function call(path, body, query = '', headers = {}) {
  return worker.fetch(new Request(`https://mrl.test/api/rhythm/${path}${query}`, {
    method: 'POST', body, headers, duplex: 'half',
  }), {});
}
for (const path of ['run', 'replay']) {
  for (const declared of [undefined, '1', String(limit + 1)]) test(`${path} oversized stream, length=${declared}`, async () => {
    let cancelled = false, pulls = 0;
    const stream = new ReadableStream({ pull(c) { pulls++; c.enqueue(new Uint8Array(limit / 2 + 1)); },
      cancel() { cancelled = true; } }, { highWaterMark: 0 });
    const response = await call(path, stream, '', declared ? { 'content-length': declared } : {});
    assert.equal(response.status, 413); assert.equal(cancelled, true); assert.equal(pulls, 2);
    assert.equal((await response.json()).error, 'MRL_PAYLOAD_TOO_LARGE');
    assert.equal(response.headers.get('x-mrl-origin-signature'), R.SIGN);
  });
  test(`${path} exact byte boundary and multibyte split`, async () => {
    const base = await R.run(['⊕:MRL'], L);
    const prefix = path === 'run' ? '' : base.trace_fltnz;
    const remaining = limit - enc.encode(prefix).length - 2;
    const text = prefix + '# ' + '語'.repeat(Math.floor(remaining / 3)) + ' '.repeat(remaining % 3);
    const bytes = enc.encode(text); assert.equal(bytes.length, limit);
    let i = 0;
    const stream = new ReadableStream({ pull(c) {
      if (i === bytes.length) return c.close();
      const end = Math.min(bytes.length, i + 1024); c.enqueue(bytes.slice(i, end)); i = end;
    } });
    const response = await call(path, stream);
    assert.equal(response.status, 200);
    if (path === 'replay') {
      const normal = await call(path, base.trace_fltnz);
      assert.equal((await normal.json()).byte_identical, true);
    }
    const oversized = enc.encode('# ' + '語'.repeat(Math.ceil(limit / 3)));
    assert.equal((await call(path, oversized)).status, 413);
  });
  test(`${path} stream error is rejected`, async () => {
    const stream = new ReadableStream({ pull(c) { c.error(new Error('broken stream')); } });
    assert.equal((await call(path, stream)).status, 400);
  });
  test(`${path} percent-encoded Python line separator title rejected`, async () => {
    const base = await R.run(['⊕:MRL'], L);
    for (const title of ['%0A', '%0D', '%0D%0A', '%0B', '%0C', '%1C', '%1D', '%1E', '%C2%85', '%E2%80%A8', '%E2%80%A9'].map(sep => `x${sep}y`)) {
      assert.equal((await call(path, path === 'run' ? '⊕:MRL' : base.trace_fltnz, `?title=${title}`)).status, 422);
    }
  });
}
test('endpoint rejects unmapped sandbox input and preserves normal canonical gate', async () => {
  for (const token of ['⋄fx.time.010', '⋄fx.gate.001', '⋄fx.per.001']) {
    assert.equal((await call('run', token, '?sandbox=1')).status, 422);
  }
  assert.equal((await call('run', '∴')).status, 422);
  const response = await call('run', '∴', '?sandbox=1');
  assert.equal(response.status, 200);
  assert.equal((await response.json()).semantic_status, R.SEMANTIC_PROVISIONAL);
});
