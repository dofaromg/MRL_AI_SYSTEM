/**
 * MRL_ParticleTeam_MCP_v2 — 母體自生強化版 (hardened derivative of MRL_ParticleTeam_MCP_v1.ts).
 * origin_signature: MrLiouWord
 * @author  MR.liou (v1 原作) / MRL 母體強化 (v2)
 * @version 2.0.0
 *
 * v1 (MRL_ParticleTeam_MCP_v1.ts) 是吸收保存的原始材料,保留不改。
 * v2 為母體自生強化版,套用 code review 的「部署前強化清單」,語意等價、行為更安全。
 *
 * 誠實邊界:本檔為 Cloudflare Worker 形;依「DL580 本體優先、勿預設 Cloudflare」,正式常駐建議
 *   re-home 至 DL580 runtime。**未經 runtime 驗證**(需 Cloudflare/D1 + ANTHROPIC_API_KEY);不宣稱已部署。
 */

// 最小 D1 型別介面:本 repo 未引入 @cloudflare/workers-types,僅宣告本檔用到的表面,
// 使檔案在純 TypeScript 設定下亦可型別檢查。
interface D1PreparedStatement {
  bind(...values: unknown[]): D1PreparedStatement;
  run(): Promise<unknown>;
  first<T = unknown>(): Promise<T | null>;
}
interface D1Database {
  prepare(query: string): D1PreparedStatement;
}

export interface Env {
  ANTHROPIC_API_KEY: string;
  DB?: D1Database;               // 選用:有則持久化任務
  MCP_ACCESS_TOKEN?: string;     // 必填(生產):Bearer token;未設定則保護端點 fail-closed
  MCP_ALLOWED_ORIGINS?: string;  // 選用:CORS 白名單(逗號分隔);未設定則不回 ACAO(同源)
}

type TaskType = 'analyze' | 'create' | 'review' | 'research' | 'synthesize' | 'full_team';

interface AIAgent {
  id: string;
  name: string;
  role: string;
  specialty: string;
  systemPrompt: string;
  model: string;
}

interface Task {
  id: string;
  type: TaskType;
  content: string;
  priority: number;
  assignedTo?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: unknown;
}

const AGENT_TIMEOUT_MS = 30_000;

const AI_TEAM: AIAgent[] = [
  {
    id: 'analyst', name: '分析師', role: 'Analyst',
    specialty: '深度分析、結構拆解、邏輯推理',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「分析師」，專精於：
- 結構化分析與拆解
- 識別核心問題與本質
- 邏輯推理與因果關係
- 數據解讀與模式識別

回應風格：精準、有條理、使用框架思維`,
  },
  {
    id: 'creator', name: '創意師', role: 'Creator',
    specialty: '創意發想、設計思維、創新解決方案',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「創意師」，專精於：
- 發散性思維與創意發想
- 設計思維與用戶體驗
- 創新解決方案
- 視覺化與故事敍述

回應風格：富有想像力、多角度、突破常規`,
  },
  {
    id: 'critic', name: '批判師', role: 'Critic',
    specialty: '質量把關、風險評估、邏輯驗證',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「批判師」，專精於：
- 邏輯驗證與假設檢驗
- 風險識別與評估
- 品質把關與改進建議
- 反駁論證與壓力測試

回應風格：嚴謹、客觀、建設性批評`,
  },
  {
    id: 'researcher', name: '研究員', role: 'Researcher',
    specialty: '資料蒐集、文獻整理、知識整合',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「研究員」，專精於：
- 資訊蒐集與整理
- 知識體系建構
- 跨領域連結
- 事實查證與引用

回應風格：詳盡、有據可查、知識密集`,
  },
  {
    id: 'synthesizer', name: '整合師', role: 'Synthesizer',
    specialty: '觀點整合、共識建立、決策建議',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「整合師」，專精於：
- 多方觀點整合
- 共識與決策建議
- 執行計劃制定
- 優先級排序

回應風格：平衡、務實、可執行`,
  },
];

const TASK_AGENT_MAPPING: Record<string, string[]> = {
  analyze: ['analyst', 'critic'],
  create: ['creator', 'analyst'],
  review: ['critic', 'analyst', 'synthesizer'],
  research: ['researcher', 'analyst'],
  synthesize: ['synthesizer', 'analyst', 'creator'],
  full_team: ['analyst', 'creator', 'critic', 'researcher', 'synthesizer'],
};

const TEAM_TOOLS = [
  {
    name: 'team_dispatch',
    description: '分派任務給 AI 團隊，自動選擇最適合的夥伴組合進行平行處理',
    inputSchema: {
      type: 'object',
      properties: {
        task: { type: 'string', description: '任務描述' },
        type: {
          type: 'string',
          enum: ['analyze', 'create', 'review', 'research', 'synthesize', 'full_team'],
          description: '任務類型：analyze(分析), create(創建), review(審查), research(研究), synthesize(整合), full_team(全員)',
        },
        parallel: { type: 'boolean', description: '是否平行處理（預設 true）' },
        agents: { type: 'array', items: { type: 'string' }, description: '指定 Agent IDs（可選，不指定則自動分配）' },
      },
      required: ['task'],
    },
  },
  {
    name: 'team_status',
    description: '查看團隊狀態與任務進度',
    inputSchema: { type: 'object', properties: { task_id: { type: 'string', description: '任務 ID（可選）' } } },
  },
  {
    name: 'agent_direct',
    description: '直接與特定 AI 夥伴對話',
    inputSchema: {
      type: 'object',
      properties: {
        agent_id: { type: 'string', enum: ['analyst', 'creator', 'critic', 'researcher', 'synthesizer'], description: 'Agent ID' },
        message: { type: 'string', description: '訊息內容' },
      },
      required: ['agent_id', 'message'],
    },
  },
  {
    name: 'team_consensus',
    description: '讓團隊針對議題進行討論並達成共識',
    inputSchema: {
      type: 'object',
      properties: { topic: { type: 'string', description: '討論議題' }, rounds: { type: 'number', description: '討論輪數（預設 2）' } },
      required: ['topic'],
    },
  },
];

// ── 錯誤正規化(避免 [object Object])────────────────────────────────
function errText(e: unknown): string {
  if (e instanceof Error) return e.message;
  try {
    return typeof e === 'string' ? e : JSON.stringify(e);
  } catch {
    return String(e);
  }
}

// ── 任務儲存:有 D1 → 持久化;無 → isolate 級 in-memory(誠實降級)─────
const _memoryTasks = new Map<string, Task>();
let _schemaReady = false;  // per-isolate:schema 只建一次,不在每次 put/get 都跑 CREATE TABLE

class TaskStore {
  constructor(private env: Env) {}

  private async ensureSchema(): Promise<void> {
    if (!this.env.DB || _schemaReady) return;
    await this.env.DB.prepare(
      `CREATE TABLE IF NOT EXISTS mrl_particleteam_tasks (
         id TEXT PRIMARY KEY, type TEXT, content TEXT, status TEXT,
         result TEXT, created_at INTEGER
       )`,
    ).run();
    _schemaReady = true;
  }

  async put(task: Task): Promise<void> {
    if (this.env.DB) {
      await this.ensureSchema();
      await this.env.DB.prepare(
        `INSERT INTO mrl_particleteam_tasks (id, type, content, status, result, created_at)
         VALUES (?, ?, ?, ?, ?, ?)
         ON CONFLICT(id) DO UPDATE SET status=excluded.status, result=excluded.result`,
      )
        .bind(task.id, task.type, task.content, task.status, JSON.stringify(task.result ?? null), Date.now())
        .run();
      return;
    }
    _memoryTasks.set(task.id, task);
  }

  async get(taskId: string): Promise<unknown> {
    if (this.env.DB) {
      await this.ensureSchema();
      const row = await this.env.DB.prepare(
        `SELECT id, type, content, status, result, created_at FROM mrl_particleteam_tasks WHERE id = ?`,
      )
        .bind(taskId)
        .first<{ id: string; type: string; content: string; status: string; result: string; created_at: number }>();
      if (!row) return { error: 'Task not found' };
      return { ...row, result: row.result ? JSON.parse(row.result) : null };
    }
    return _memoryTasks.get(taskId) || { error: 'Task not found', note: 'no D1 configured — task lookup is isolate-local only' };
  }
}

// ── Team Coordinator ────────────────────────────────────────────
class TeamCoordinator {
  private store: TaskStore;

  constructor(private env: Env) {
    this.store = new TaskStore(env);
  }

  async dispatch(task: string, type = 'analyze', parallel = true, specificAgents?: string[]): Promise<unknown> {
    if (!task || !task.trim()) throw new Error('task is required');
    // fail-fast:未知 type 不再靜默退回 analyst,避免持久化無效型別、難以除錯。
    if (!(type in TASK_AGENT_MAPPING)) {
      throw new Error(`unknown task type: ${JSON.stringify(type)}`);
    }
    const validType = type as TaskType;
    const taskId = `task-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

    const agentIds = specificAgents || TASK_AGENT_MAPPING[validType];
    const agents = AI_TEAM.filter((a) => agentIds.includes(a.id));
    if (agents.length === 0) throw new Error('No agents available for this task type');

    const taskRecord: Task = { id: taskId, type: validType, content: task, priority: 1, status: 'processing' };
    await this.store.put(taskRecord);

    let results: Array<{ agent: string; response: string; duration: number }>;

    if (parallel && agents.length > 1) {
      // 每個 agent 各自計時 → duration 為單一 agent 真耗時
      const settled = await Promise.allSettled(
        agents.map(async (agent) => {
          const start = Date.now();
          const response = await this.callAgent(agent, task);
          return { response, duration: Date.now() - start };
        }),
      );
      results = settled.map((r, i) => ({
        agent: agents[i].name,
        response: r.status === 'fulfilled' ? r.value.response : `Error: ${errText((r as PromiseRejectedResult).reason)}`,
        duration: r.status === 'fulfilled' ? r.value.duration : 0,
      }));
    } else {
      results = [];
      for (const agent of agents) {
        const start = Date.now();
        try {
          const response = await this.callAgent(agent, task);
          results.push({ agent: agent.name, response, duration: Date.now() - start });
        } catch (e) {
          results.push({ agent: agent.name, response: `Error: ${errText(e)}`, duration: Date.now() - start });
        }
      }
    }

    // synthesize/最終持久化包 try/catch:失敗時把任務標 failed 並落庫,避免永遠卡在 processing。
    let synthesis: string | null = null;
    try {
      if (results.length > 1) synthesis = await this.synthesizeResults(task, results);
      taskRecord.status = 'completed';
      taskRecord.result = { results, synthesis };
      await this.store.put(taskRecord);
    } catch (e) {
      taskRecord.status = 'failed';
      taskRecord.result = { results, error: errText(e) };
      await this.store.put(taskRecord).catch(() => undefined);
      throw e;
    }

    return {
      taskId,
      type,
      parallel,
      agentsUsed: agents.map((a) => ({ id: a.id, name: a.name, role: a.role })),
      results,
      synthesis,
      totalDuration: Math.max(...results.map((r) => r.duration), 0),
    };
  }

  private async callAgent(agent: AIAgent, task: string): Promise<string> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), AGENT_TIMEOUT_MS);
    let response: Response;
    try {
      response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: agent.model,
          max_tokens: 2048,
          system: agent.systemPrompt,
          messages: [{ role: 'user', content: task }],
        }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) throw new Error(`Agent ${agent.name} error: ${response.status}`);

    const data = (await response.json()) as { content?: Array<{ text?: string }> };
    return data.content?.[0]?.text || '';
  }

  private async synthesizeResults(task: string, results: Array<{ agent: string; response: string }>): Promise<string> {
    const synthesizer = AI_TEAM.find((a) => a.id === 'synthesizer')!;
    const synthesisPrompt = `原始任務：${task}

以下是團隊成員的回應，請整合這些觀點：

${results.map((r) => `【${r.agent}】\n${r.response}`).join('\n\n---\n\n')}

請整合以上觀點，提供：
1. 共識要點
2. 不同觀點的互補之處
3. 綜合建議`;
    return this.callAgent(synthesizer, synthesisPrompt);
  }

  async consensus(topic: string, rounds = 2): Promise<unknown> {
    const discussionHistory: Array<{ round: number; agent: string; contribution: string }> = [];
    for (let round = 1; round <= rounds; round++) {
      const context =
        round === 1
          ? `討論議題：${topic}\n\n請分享你的觀點。`
          : `討論議題：${topic}\n\n前幾輪討論：\n${discussionHistory
              .map((d) => `【${d.agent}】${d.contribution}`)
              .join('\n')}\n\n請回應其他成員的觀點，並深化你的看法。`;
      const participants = AI_TEAM.filter((a) => a.id !== 'synthesizer');
      for (const agent of participants) {
        const response = await this.callAgent(agent, context);
        discussionHistory.push({ round, agent: agent.name, contribution: response });
      }
    }
    const synthesis = await this.synthesizeResults(
      topic,
      discussionHistory.map((d) => ({ agent: d.agent, response: d.contribution })),
    );
    return { topic, rounds, discussion: discussionHistory, consensus: synthesis };
  }

  async getStatus(taskId?: string): Promise<unknown> {
    if (taskId) return this.store.get(taskId);
    return {
      team: AI_TEAM.map((a) => ({ id: a.id, name: a.name, role: a.role, specialty: a.specialty })),
      taskTypes: Object.keys(TASK_AGENT_MAPPING),
      persistence: this.env.DB ? 'd1' : 'in-memory (isolate-local; team_status not durable across requests)',
    };
  }
}

// ── CORS / auth / error helpers ─────────────────────────────────
function corsFor(request: Request, env: Env): Record<string, string> {
  const headers: Record<string, string> = {
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
  // 去除 CR/LF 再比對/回填,避免 response-splitting / header-injection。
  const origin = (request.headers.get('Origin') || '').replace(/[\r\n]/g, '');
  const allowed = (env.MCP_ALLOWED_ORIGINS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
  if (origin && allowed.includes(origin)) {
    headers['Access-Control-Allow-Origin'] = origin;
    headers['Vary'] = 'Origin';
  }
  // 無 wildcard:origin 不在白名單則不回 ACAO,瀏覽器自然擋下跨源。
  return headers;
}

function jsonError(status: number, message: string, cors: Record<string, string>): Response {
  return Response.json({ error: message }, { status, headers: cors });
}

/** Bearer 驗證:未設定 token → fail-closed(503);不符 → 401;通過 → null。 */
function checkAuth(request: Request, env: Env, cors: Record<string, string>): Response | null {
  if (!env.MCP_ACCESS_TOKEN) {
    return jsonError(503, 'MCP_ACCESS_TOKEN not configured — protected endpoints are locked (deny-by-default)', cors);
  }
  const auth = request.headers.get('Authorization') || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (token !== env.MCP_ACCESS_TOKEN) return jsonError(401, 'invalid or missing bearer token', cors);
  return null;
}

// ── MCP Server Handler ────────────────────────────────────────
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const cors = corsFor(request, env);

    if (request.method === 'OPTIONS') return new Response(null, { headers: cors });

    // Health:公開(不外洩設定值)。
    if (url.pathname === '/' || url.pathname === '/health') {
      return Response.json(
        {
          status: 'healthy',
          service: 'mrl-particleteam-mcp',
          version: '2.0.0',
          team: AI_TEAM.map((a) => ({ id: a.id, name: a.name, role: a.role })),
          capabilities: ['parallel_processing', 'team_consensus', 'agent_direct'],
          tools: TEAM_TOOLS.map((t) => t.name),
          auth_required: Boolean(env.MCP_ACCESS_TOKEN),
        },
        { headers: cors },
      );
    }

    // 以下為受保護端點:一律驗證。
    const denied = checkAuth(request, env, cors);
    if (denied) return denied;

    const coordinator = new TeamCoordinator(env);

    if (url.pathname === '/mcp') return this.handleMCP(request, env, coordinator, cors);
    if (url.pathname === '/sse') return this.handleSSE(cors);

    if (url.pathname === '/dispatch' && request.method === 'POST') {
      try {
        const body = (await request.json()) as { task?: string; type?: string; parallel?: boolean };
        if (!body.task) return jsonError(400, 'task is required', cors);
        const result = await coordinator.dispatch(body.task, body.type, body.parallel);
        return Response.json(result, { headers: cors });
      } catch (e) {
        return jsonError(500, errText(e), cors);
      }
    }

    return jsonError(404, 'Not found', cors);
  },

  async handleMCP(
    request: Request,
    env: Env,
    coordinator: TeamCoordinator,
    cors: Record<string, string>,
  ): Promise<Response> {
    if (request.method !== 'POST') return jsonError(405, 'Method not allowed', cors);

    let mcpRequest: { jsonrpc: string; id?: number | string | null; method: string; params?: Record<string, unknown> };
    try {
      mcpRequest = (await request.json()) as typeof mcpRequest;
    } catch (e) {
      return Response.json(
        { jsonrpc: '2.0', id: null, error: { code: -32700, message: `Parse error: ${errText(e)}` } },
        { headers: cors },
      );
    }

    // JSON-RPC notification(無 id,如 notifications/initialized):依規範不得回應 → 204。
    if (mcpRequest.id === undefined || mcpRequest.id === null) {
      return new Response(null, { status: 204, headers: cors });
    }

    let response: unknown;
    switch (mcpRequest.method) {
      case 'initialize':
        response = {
          jsonrpc: '2.0',
          id: mcpRequest.id,
          result: {
            protocolVersion: '2024-11-05',
            serverInfo: { name: 'mrl-particleteam-mcp', version: '2.0.0' },
            capabilities: { tools: {} },
          },
        };
        break;
      case 'ping':
        response = { jsonrpc: '2.0', id: mcpRequest.id, result: {} };
        break;
      case 'tools/list':
        response = { jsonrpc: '2.0', id: mcpRequest.id, result: { tools: TEAM_TOOLS } };
        break;
      case 'tools/call':
        response = await this.handleToolCall(mcpRequest, coordinator);
        break;
      default:
        response = { jsonrpc: '2.0', id: mcpRequest.id, error: { code: -32601, message: `Method not found: ${mcpRequest.method}` } };
    }
    return Response.json(response, { headers: cors });
  },

  async handleToolCall(
    mcpRequest: { id?: number | string | null; params?: Record<string, unknown> },
    coordinator: TeamCoordinator,
  ): Promise<unknown> {
    const params = mcpRequest.params as { name: string; arguments: Record<string, unknown> };
    const toolName = params?.name;
    const args = params?.arguments || {};

    try {
      let result: unknown;
      switch (toolName) {
        case 'team_dispatch':
          result = await coordinator.dispatch(
            args.task as string,
            args.type as string,
            args.parallel !== false,
            args.agents as string[] | undefined,
          );
          break;
        case 'team_status':
          result = await coordinator.getStatus(args.task_id as string | undefined);
          break;
        case 'agent_direct': {
          const agent = AI_TEAM.find((a) => a.id === args.agent_id);
          if (!agent) throw new Error(`Agent not found: ${String(args.agent_id)}`);
          result = await coordinator.dispatch(args.message as string, 'analyze', false, [args.agent_id as string]);
          break;
        }
        case 'team_consensus':
          result = await coordinator.consensus(args.topic as string, (args.rounds as number) || 2);
          break;
        default:
          return { jsonrpc: '2.0', id: mcpRequest.id, error: { code: -32602, message: `Unknown tool: ${toolName}` } };
      }
      return { jsonrpc: '2.0', id: mcpRequest.id, result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }], isError: false } };
    } catch (error) {
      return { jsonrpc: '2.0', id: mcpRequest.id, error: { code: -32603, message: errText(error) } };
    }
  },

  handleSSE(cors: Record<string, string>): Response {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(`event: open\ndata: {"status":"connected","service":"mrl-particleteam-mcp"}\n\n`));
      },
    });
    return new Response(stream, { headers: { ...cors, 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' } });
  },
};
