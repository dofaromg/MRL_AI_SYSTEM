#!/usr/bin/env node
// MRL_metacode_recovery_smoke_v1.mjs
// origin_signature: MrLiouWord
// SUPPLEMENT_EXISTING: verify the recovered original and its unchanged usage.
// Run: node --experimental-vm-modules scripts/MRL_metacode_recovery_smoke_v1.mjs
// Optional DL580 persistence: append --output-dir D:\MRL_Mother\EvidenceChain\MetaCode
// Default: memory-only usage exports; stdout contains metadata, never source contents.

import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';

const SOURCE = {
  core: {
    path: 'metacode_core.js',
    repository: 'dofaromg/flow-tasks',
    ref: 'cb73e661a02eeb540db02398cb61eaa51c5e77e3',
    source_path: 'metacode_core.js',
    first_commit: 'f4d7637a6a66fa0256508dd6759dc23efdae689d',
    first_commit_utc: '2026-01-27T05:30:23Z',
    bytes: 15198,
    git_blob_sha1: '39b1bb6e8ef4dfce3ea0d8cc01fe38ab8721f7bd',
    sha256: 'ae5da0117f32f9795a99d5e5774fa38e5f5314cacbd7e289eaa9b440bd6fa158'
  },
  usage: {
    path: 'metacode_usage.js',
    repository: 'dofaromg/flow-tasks',
    ref: 'cb73e661a02eeb540db02398cb61eaa51c5e77e3',
    source_path: 'MRL_Mother/root_sources/metacode_usage.js',
    bytes: 14901,
    git_blob_sha1: '8ea6a6f6f51f1923990e0d0b147ffc4b91d6d5b6',
    sha256: 'ee51df5d38dc914a947b6e3809e0e97969f90eedc844c23d05c36ae8409d6da8'
  }
};
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const checks = [];
function check(label, run) { run(); checks.push({ check: label, status: 'PASS' }); }

function parseOptions(args) {
  if (!args.length) return { outputDir: null };
  if (args.length === 2 && args[0] === '--output-dir' && args[1]) return { outputDir: args[1] };
  throw new Error('Usage: node --experimental-vm-modules scripts/MRL_metacode_recovery_smoke_v1.mjs [--output-dir D:\\path]');
}

function ensureLocalOutputRoot(requested) {
  if (!requested) return null;
  assert.equal(process.platform, 'win32', 'Persistent output requires the DL580 Windows host.');
  assert.equal(os.hostname().toUpperCase(), 'WIN-PBVUI7VK2A6', 'Persistent output requires the recorded DL580 host.');
  assert.match(requested, /^D:\\/i, 'Persistent output must use an absolute D: path.');
  const parent = path.win32.resolve(requested);
  let ancestor = parent;
  while (!fs.existsSync(ancestor)) {
    const next = path.win32.dirname(ancestor);
    assert.notEqual(next, ancestor, 'D: ancestor must exist.');
    ancestor = next;
  }
  assert.match(fs.realpathSync(ancestor), /^D:\\/i, 'Output ancestor must resolve to local D:.');
  fs.mkdirSync(parent, { recursive: true });
  assert.match(fs.realpathSync(parent), /^D:\\/i, 'Output directory must resolve to local D:.');
  return fs.mkdtempSync(path.join(parent, 'MRL_MetaCode_Recovery_'));
}

async function main() {
  const options = parseOptions(process.argv.slice(2));
  assert.equal(typeof vm.SourceTextModule, 'function', 'Use Node with --experimental-vm-modules.');
  const sourceBuffers = {};
  for (const [name, expected] of Object.entries(SOURCE)) {
    const bytes = fs.readFileSync(new URL('../' + expected.path, import.meta.url));
    sourceBuffers[name] = bytes;
    check(name + ': original bytes and hashes', () => {
      assert.equal(bytes.length, expected.bytes);
      assert.equal(hash(bytes), expected.sha256);
      assert.equal(crypto.createHash('sha1').update('blob ' + bytes.length + '\0').update(bytes).digest('hex'), expected.git_blob_sha1);
    });
  }

  const writes = new Map(), directories = new Set(), logs = [], errors = [];
  const memoryFS = {
    existsSync: (p) => directories.has(p),
    mkdirSync: (p) => { directories.add(p); },
    writeFileSync: (p, bytes) => { writes.set(p, Buffer.from(bytes)); }
  };
  const context = vm.createContext({
    console: { log: (...args) => logs.push(args.map(String).join(' ')), error: (...args) => errors.push(args.map(String).join(' ')) },
    process: { argv: ['mrl-memory-usage'] }
  });
  const core = new vm.SourceTextModule(sourceBuffers.core.toString('utf8'), { context, identifier: 'mrl-memory:///metacode_core.js' });
  const usage = new vm.SourceTextModule(sourceBuffers.usage.toString('utf8'), { context, identifier: 'mrl-memory:///metacode_usage.js' });
  const modules = new Map();
  for (const [name, value] of [['crypto', crypto], ['fs', memoryFS], ['path', path]]) {
    modules.set(name, new vm.SyntheticModule(['default'], function () { this.setExport('default', value); }, { context }));
  }
  function link(specifier) {
    if (specifier === './metacode_core.js') return core;
    const module = modules.get(specifier);
    if (!module) throw new Error('Unexpected import in original source.');
    return module;
  }
  await core.link(link); await core.evaluate();
  await usage.link(link); await usage.evaluate();
  await new Promise((resolve) => setImmediate(resolve));

  check('unchanged usage: all seven scenarios complete', () => {
    assert.equal(errors.length, 0);
    assert.equal(writes.size, 5);
    assert.equal(logs.some((s) => s.includes('PASSED')), true);
    assert.equal(logs.some((s) => s.includes('FAILED')), false);
    assert.equal(logs.some((s) => s.includes('執行完成')), true);
  });
  const full = [...writes].find(([p]) => /^data[\\/]MetaCode\.export\..*\.json$/.test(p));
  assert.ok(full, 'Full usage export must be present.');
  const exported = JSON.parse(full[1].toString('utf8'));
  check('original export shape and original version', () => {
    assert.equal(exported.meta.version, '2.0.0-alpha');
    assert.equal(exported.particles.length, 7);
    assert.equal(exported.links.length, 3);
    assert.equal(exported.cycles.length, 2);
    assert.ok(exported.journal.length > 0);
    assert.ok(exported.self);
  });
  check('all five usage outputs nonempty and parseable', () => {
    for (const [p, bytes] of writes) {
      assert.ok(bytes.length > 0);
      if (p.endsWith('.jsonl')) for (const line of bytes.toString('utf8').split('\n')) JSON.parse(line);
      else JSON.parse(bytes.toString('utf8'));
    }
  });

  const MetaCode = core.namespace.default;
  const meta = new MetaCode();
  const a = meta.createParticle({ mag: 2, N: 10, eta: 0.9, domain: 'math', zoom: 0.6 });
  const b = meta.createParticle({ mag: 2, N: 10, eta: 0.9, domain: 'math', zoom: 0.6 });
  check('original P * N * eta and trace domain', () => {
    assert.equal(a.amplify.present, 18);
    assert.equal(a.trace.domain, 'math');
  });
  check('original bind decision vocabulary', () => assert.equal(meta.matchParticle(b).decision, 'bind'));
  meta.createLink(a.id, b.id, 'recovery-verification');
  const imported = new MetaCode();
  imported.import(meta.export());
  check('original import/export keeps the dependency graph', () => {
    assert.equal(imported.particles.size, 2);
    assert.equal(imported.links.size, 1);
    assert.equal(imported.verify().ok, true);
  });

  const receipt = {
    schema: 'MRL_MetaCode_Recovery_Receipt_v1',
    origin_signature: 'MrLiouWord',
    record_mode: 'additive_only',
    checked_at_utc: new Date().toISOString(),
    environment: {
      hostname: os.hostname(),
      platform: process.platform,
      node_version: process.version,
      dl580_host_match: process.platform === 'win32' && os.hostname().toUpperCase() === 'WIN-PBVUI7VK2A6'
    },
    gate: 'METACODE_SOURCE_AND_USAGE_PASS',
    scope: 'Original source integrity and the unchanged seven usage scenarios; no model, network, ASI or watchdog acceptance.',
    source_files: Object.values(SOURCE),
    checks,
    output_mode: options.outputDir ? 'DL580_D_DRIVE' : 'MEMORY_ONLY',
    usage_output_count: writes.size,
    usage_outputs: [...writes].map(([p, bytes]) => ({ path: p.split(path.sep).join('/'), bytes: bytes.length, sha256: hash(bytes) }))
  };
  const outputRoot = ensureLocalOutputRoot(options.outputDir);
  if (outputRoot) {
    for (const [p, bytes] of writes) {
      const target = path.join(outputRoot, p);
      assert.ok(target.startsWith(outputRoot + path.sep), 'Usage output must remain inside its new run directory.');
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, bytes, { flag: 'wx' });
      assert.equal(hash(fs.readFileSync(target)), hash(bytes), 'Saved usage bytes must match.');
    }
    receipt.output_directory = outputRoot;
    const target = path.join(outputRoot, 'MRL_metacode_recovery_receipt_v1.json');
    receipt.receipt_path = target;
    fs.writeFileSync(target, JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
  }
  process.stdout.write(JSON.stringify(receipt, null, 2) + '\n');
}
try { await main(); }
catch (error) {
  process.stderr.write(JSON.stringify({ gate: 'METACODE_SOURCE_AND_USAGE_FAIL', error: error.message }) + '\n');
  process.exitCode = 1;
}
