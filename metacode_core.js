/**
 * METACODE 核心（metacode_core.js）
 * ────────────────────────────────────────────────────────────
 * Mr.L-Code 元代碼引擎 — 跨域粒子演化與一致性匹配。
 *
 * 本檔為「重建版」：原始 metacode_core.js 真身未尋獲（DL580 / 外部 repo）。
 * 依據以下三份母體材料重建，以 metacode_usage.js 七場景全數跑通為驗收標準：
 *   1) MrL_Metacode_元代碼定義_v1.txt — Mr.L-Code 文法
 *      Particle → Route(P,μ) → Tensor → DimensionProjection(d) → Collapse(J)
 *   2) metacode_usage.js — 對外 API 面（九方法）
 *   3) FlowAgent×MRL×MetaCode 三系統整合分析 — P·N·η 創世公式、三層決策、傳播機制
 *
 * origin_signature: MrLiouWord
 * 誠實標註：重建版，非原檔；行為以「範例可跑通」為界，非宣稱與原檔逐位元等價。
 */

import crypto from 'crypto';

// ── 場域路由表：粒子 domain / tag → Mr.L-Code 場域 μ ──────────────
const FIELD_ROUTES = {
  math: 'MindField',
  storage: 'MatterField',
  compute: 'WaveField',
  flowagent: 'MindField',
  unified: 'MindField',
  unknown: 'MindField'
};

function clamp01(x) {
  if (Number.isNaN(x)) return 0;
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

function shortHash(obj) {
  return crypto.createHash('sha256')
    .update(JSON.stringify(obj))
    .digest('hex');
}

export default class MetaCode {
  constructor() {
    this.id = `metacode-${shortHash({ t: 'root', r: crypto.randomBytes(8).toString('hex') }).slice(0, 24)}`;
    this.version = '1.0.0-reconstructed';
    this.particles = new Map(); // id → particle
    this.links = [];            // { from, to, relation, ts_seq }
    this.cycles = [];           // 演化週期紀錄
    this.journal = [];          // 事件日誌
    this._seq = 0;              // 單調序號（取代時間戳，確保可重現）
  }

  _tick() { return ++this._seq; }

  _log(type, detail) {
    this.journal.push({ seq: this._tick(), type, detail });
  }

  // ── 放大公式：創世公式 P_{k+1} = N · P · η 的落地 ──────────────
  // present capacity = mag(基礎能量 P) × N(層級堆疊) × η(效率)，
  // 由 conf(信度) 微調（低信度折損能力）。
  _amplify({ mag, N, eta, conf }) {
    const present = mag * N * eta * (0.5 + 0.5 * conf);
    return { N, eta, mag, conf, present };
  }

  // 1) createParticle —— 粒子化 + Route(P,μ) + Tensor + 放大
  createParticle(spec = {}) {
    const {
      domain = 'unknown',
      mag = 1.0,
      zoom = 0.5,
      surprisal = 0.5,
      conf = 0.8,
      N = 1,
      eta = 0.8,
      tags = []
    } = spec;

    const field = FIELD_ROUTES[domain] || 'MindField';
    const axes = { zoom: clamp01(zoom), surprisal: clamp01(surprisal), conf: clamp01(conf), mag };
    const id = `mrl-particle::${domain}::${field}::${shortHash({ domain, axes, N, eta, tags, seq: this._seq })}`;

    const particle = {
      id,
      domain,
      field,                 // Route(P,μ)
      tags: [...tags],
      cap: { axes },         // 觀察軸（zoom/surprisal/conf/mag）
      tensor: {              // Tensor 結構（Mr.L-Code）
        particles: tags.length ? [...tags] : [domain],
        rhythm: `${Math.max(1, Math.round(N / Math.max(1, N > 100 ? 50 : 10)))}:1`,
        persona: domain
      },
      amplify: this._amplify({ mag, N, eta, conf }),
      created_seq: this._tick()
    };

    this.particles.set(id, particle);
    this._log('create', { id, domain, present: particle.amplify.present });
    return particle;
  }

  // 2) evolveParticle —— 更新 N/η 等，重算放大（牽動 present）
  evolveParticle(id, delta = {}) {
    const p = this.particles.get(id);
    if (!p) throw new Error(`evolveParticle: 找不到粒子 ${id}`);
    const before = p.amplify.present;
    const N = delta.N != null ? delta.N : p.amplify.N;
    const eta = delta.eta != null ? clamp01(delta.eta) : p.amplify.eta;
    const mag = delta.mag != null ? delta.mag : p.amplify.mag;
    const conf = delta.conf != null ? clamp01(delta.conf) : p.amplify.conf;
    p.amplify = this._amplify({ mag, N, eta, conf });
    if (delta.zoom != null) p.cap.axes.zoom = clamp01(delta.zoom);

    this.cycles.push({
      seq: this._tick(), kind: 'evolve', id,
      before, after: p.amplify.present, delta: { N, eta }
    });
    this._log('evolve', { id, before, after: p.amplify.present });
    return p;
  }

  // 3) createLink —— 建立粒子間關聯（依賴圖的邊）
  createLink(from, to, relation = 'related') {
    if (!this.particles.has(from)) throw new Error(`createLink: 來源粒子不存在 ${from}`);
    if (!this.particles.has(to)) throw new Error(`createLink: 目標粒子不存在 ${to}`);
    const link = { from, to, relation, seq: this._tick() };
    this.links.push(link);
    this._log('link', { from, to, relation });
    return link;
  }

  // 4) calculateSimilarity —— 跨域一致性：軸距 + 標籤重疊
  calculateSimilarity(a, b) {
    if (!a || !b) return 0;
    const ax = a.cap.axes, bx = b.cap.axes;
    // 軸相似度（zoom/surprisal/conf 距離越近越像）
    const axisKeys = ['zoom', 'surprisal', 'conf'];
    let axisSim = 0;
    for (const k of axisKeys) axisSim += 1 - Math.abs((ax[k] ?? 0) - (bx[k] ?? 0));
    axisSim /= axisKeys.length;
    // 標籤 Jaccard
    const ta = new Set(a.tags || []), tb = new Set(b.tags || []);
    let inter = 0;
    for (const t of ta) if (tb.has(t)) inter++;
    const union = new Set([...ta, ...tb]).size;
    const tagSim = union === 0 ? 0 : inter / union;
    // 同域加成
    const domainBonus = a.domain === b.domain ? 1 : 0;
    // 加權合成
    const score = 0.6 * axisSim + 0.3 * tagSim + 0.1 * domainBonus;
    return clamp01(score);
  }

  // 5) matchParticle —— 三層決策（absorb / link / spawn）
  matchParticle(particle) {
    let best = null, bestScore = -1;
    for (const p of this.particles.values()) {
      if (p.id === particle.id) continue;
      const s = this.calculateSimilarity(particle, p);
      if (s > bestScore) { bestScore = s; best = p; }
    }
    let decision, reason;
    if (best == null) {
      decision = 'spawn';
      reason = '無既有粒子可比對，作為新粒子生成';
    } else if (bestScore >= 0.85) {
      decision = 'absorb';
      reason = `與 ${best.domain} 粒子高度一致（${(bestScore * 100).toFixed(1)}%），吸收合併`;
    } else if (bestScore >= 0.6) {
      decision = 'link';
      reason = `與 ${best.domain} 粒子部分一致（${(bestScore * 100).toFixed(1)}%），建立關聯`;
    } else {
      decision = 'spawn';
      reason = `與最近粒子（${best.domain}）僅 ${(bestScore * 100).toFixed(1)}% 一致，另立新粒子`;
    }
    this._log('match', { id: particle.id, decision, score: bestScore });
    return { decision, reason, score: bestScore, best: best ? best.id : null };
  }

  // 6) propagate —— 變化傳播（牽一髮動全身）：沿 link 影響下游粒子
  propagate(id, opts = {}) {
    const factor = opts.factor != null ? opts.factor : 0.5;
    const affected = [];
    const seen = new Set([id]);
    let frontier = [id];
    while (frontier.length) {
      const next = [];
      for (const cur of frontier) {
        for (const link of this.links) {
          if (link.from !== cur || seen.has(link.to)) continue;
          seen.add(link.to);
          const p = this.particles.get(link.to);
          if (!p) continue;
          // 上游演化 → 下游效率微幅共振（趨近上游 η）
          const src = this.particles.get(cur);
          if (src) {
            const before = p.amplify.present;
            const newEta = clamp01(p.amplify.eta + factor * (src.amplify.eta - p.amplify.eta) * 0.1);
            p.amplify = this._amplify({ mag: p.amplify.mag, N: p.amplify.N, eta: newEta, conf: p.amplify.conf });
            affected.push({ id: p.id, before, after: p.amplify.present });
          }
          next.push(link.to);
        }
      }
      frontier = next;
    }
    this.cycles.push({ seq: this._tick(), kind: 'propagate', id, affected: affected.length });
    this._log('propagate', { id, affected: affected.length });
    return affected;
  }

  // 7) verify —— 自我驗證：關聯完整性、參數合法性
  verify() {
    const errors = [];
    for (const link of this.links) {
      if (!this.particles.has(link.from))
        errors.push({ type: 'dangling_link', message: `link.from 不存在: ${link.from}` });
      if (!this.particles.has(link.to))
        errors.push({ type: 'dangling_link', message: `link.to 不存在: ${link.to}` });
    }
    for (const p of this.particles.values()) {
      const { eta, N } = p.amplify;
      if (eta < 0 || eta > 1)
        errors.push({ type: 'bad_eta', message: `${p.id} η 超出 [0,1]: ${eta}` });
      if (!(N >= 0))
        errors.push({ type: 'bad_N', message: `${p.id} N 非法: ${N}` });
      const z = p.cap.axes.zoom;
      if (z < 0 || z > 1)
        errors.push({ type: 'bad_zoom', message: `${p.id} zoom 超出 [0,1]: ${z}` });
    }
    return { ok: errors.length === 0, errors };
  }

  // 8) calculateMetrics —— 系統指標
  calculateMetrics() {
    const parts = [...this.particles.values()];
    const total_particles = parts.length;
    const total_links = this.links.length;
    const total_cycles = this.cycles.length;
    const avg_eta = total_particles
      ? parts.reduce((s, p) => s + p.amplify.eta, 0) / total_particles
      : 0;
    // coverage：有關聯的粒子佔比（連通覆蓋率）
    const linked = new Set();
    for (const l of this.links) { linked.add(l.from); linked.add(l.to); }
    const coverage = total_particles ? linked.size / total_particles : 0;
    // spawn_rate：演化/生成事件相對粒子數的比率
    const spawn_events = this.journal.filter(j => j.type === 'create').length;
    const spawn_rate = total_particles ? spawn_events / (total_particles + total_cycles || 1) : 0;
    const domains = [...new Set(parts.map(p => p.domain))];
    return { total_particles, total_links, total_cycles, coverage, spawn_rate, avg_eta, domains };
  }

  // 9) export —— 完整導出（粒子/關聯/週期/日誌）
  export() {
    return {
      meta: { id: this.id, version: this.version },
      particles: [...this.particles.values()],
      links: [...this.links],
      cycles: [...this.cycles],
      journal: [...this.journal]
    };
  }
}
