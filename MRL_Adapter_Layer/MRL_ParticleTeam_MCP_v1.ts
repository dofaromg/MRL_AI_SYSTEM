/**
 * Particle Team MCP Server - AI 團隊協作系統
 * 支援多個 AI 夥伴平行處理任務
 *
 * @author MR.liou
 * @version 1.0.0
 *
 * 架構：
 * ┌─────────────────────────────────────────────────┐
 * │                    Team Coordinator                      │
 * │              (任務分配 & 結果整合)                        │
 * └─────────────────────┬──────────────────────────────┘
 *                       │
 *        ┌──────────────┼──────────────┐
 *        ▼              ▼              ▼
 *   ┌─────────┐   ┌─────────┐   ┌─────────┐
 *   │ Agent-A │   │ Agent-B │   │ Agent-C │
 *   │ 分析師  │   │ 創意師  │   │ 批判師  │
 *   └─────────┘   └─────────┘   └─────────┘
 */

export interface Env {
  ANTHROPIC_API_KEY: string;
  DB: D1Database;
}

// AI 夥伴角色定義
interface AIAgent {
  id: string;
  name: string;
  role: string;
  specialty: string;
  systemPrompt: string;
  model: string;
}

// 任務定義
interface Task {
  id: string;
  type: 'analyze' | 'create' | 'review' | 'research' | 'synthesize';
  content: string;
  priority: number;
  assignedTo?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: unknown;
}

// 團隊配置
const AI_TEAM: AIAgent[] = [
  {
    id: 'analyst',
    name: '分析師',
    role: 'Analyst',
    specialty: '深度分析、結構拆解、邏輯推理',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「分析師」，專精於：
- 結構化分析與拆解
- 識別核心問題與本質
- 邏輯推理與因果關係
- 數據解讀與模式識別

回應風格：精準、有條理、使用框架思維`
  },
  {
    id: 'creator',
    name: '創意師',
    role: 'Creator',
    specialty: '創意發想、設計思維、創新解決方案',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「創意師」，專精於：
- 發散性思維與創意發想
- 設計思維與用戶體驗
- 創新解決方案
- 視覺化與故事敍述

回應風格：富有想像力、多角度、突破常規`
  },
  {
    id: 'critic',
    name: '批判師',
    role: 'Critic',
    specialty: '質量把關、風險評估、邏輯驗證',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「批判師」，專精於：
- 邏輯驗證與假設檢驗
- 風險識別與評估
- 品質把關與改進建議
- 反駁論證與壓力測試

回應風格：嚴謹、客觀、建設性批評`
  },
  {
    id: 'researcher',
    name: '研究員',
    role: 'Researcher',
    specialty: '資料蒐集、文獻整理、知識整合',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「研究員」，專精於：
- 資訊蒐集與整理
- 知識體系建構
- 跨領域連結
- 事實查證與引用

回應風格：詳盡、有據可查、知識密集`
  },
  {
    id: 'synthesizer',
    name: '整合師',
    role: 'Synthesizer',
    specialty: '觀點整合、共識建立、決策建議',
    model: 'claude-sonnet-4-20250514',
    systemPrompt: `你是「整合師」，專精於：
- 多方觀點整合
- 共識與決策建議
- 執行計劃制定
- 優先級排序

回應風格：平衡、務實、可執行`
  }
];

// 任務類型對應的最佳 Agent 組合
const TASK_AGENT_MAPPING: Record<string, string[]> = {
  'analyze': ['analyst', 'critic'],
  'create': ['creator', 'analyst'],
  'review': ['critic', 'analyst', 'synthesizer'],
  'research': ['researcher', 'analyst'],
  'synthesize': ['synthesizer', 'analyst', 'creator'],
  'full_team': ['analyst', 'creator', 'critic', 'researcher', 'synthesizer']
};

// MCP Tools 定義
const TEAM_TOOLS = [
  {
    name: 'team_dispatch',
    description: '分派任務給 AI 團隊，自動選擇最適合的夥伴組合進行平行處理',
    inputSchema: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description: '任務描述'
        },
        type: {
          type: 'string',
          enum: ['analyze', 'create', 'review', 'research', 'synthesize', 'full_team'],
          description: '任務類型：analyze(分析), create(創建), review(審查), research(研究), synthesize(整合), full_team(全員)'
        },
        parallel: {
          type: 'boolean',
          description: '是否平行處理（預設 true）'
        },
        agents: {
          type: 'array',
          items: { type: 'string' },
          description: '指定 Agent IDs（可選，不指定則自動分配）'
        }
      },
      required: ['task']
    }
  },
  {
    name: 'team_status',
    description: '查看團隊狀態與任務進度',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: {
          type: 'string',
          description: '任務 ID（可選）'
        }
      }
    }
  },
  {
    name: 'agent_direct',
    description: '直接與特定 AI 夥伴對話',
    inputSchema: {
      type: 'object',
      properties: {
        agent_id: {
          type: 'string',
          enum: ['analyst', 'creator', 'critic', 'researcher', 'synthesizer'],
          description: 'Agent ID'
        },
        message: {
          type: 'string',
          description: '訊息內容'
        }
      },
      required: ['agent_id', 'message']
    }
  },
  {
    name: 'team_consensus',
    description: '讓團隊針對議題進行討論並達成共識',
    inputSchema: {
      type: 'object',
      properties: {
        topic: {
          type: 'string',
          description: '討論議題'
        },
        rounds: {
          type: 'number',
          description: '討論輪數（預設 2）'
        }
      },
      required: ['topic']
    }
  }
];

// Team Coordinator - 任務協調器
class TeamCoordinator {
  private env: Env;
  private activeTasks: Map<string, Task> = new Map();

  constructor(env: Env) {
    this.env = env;
  }

  // 分派任務給適合的 Agents
  async dispatch(task: string, type: string = 'analyze', parallel: boolean = true, specificAgents?: string[]): Promise<unknown> {
    const taskId = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // 決定使用哪些 Agents
    const agentIds = specificAgents || TASK_AGENT_MAPPING[type] || ['analyst'];
    const agents = AI_TEAM.filter(a => agentIds.includes(a.id));

    if (agents.length === 0) {
      throw new Error('No agents available for this task type');
    }

    // 記錄任務
    const taskRecord: Task = {
      id: taskId,
      type: type as Task['type'],
      content: task,
      priority: 1,
      status: 'processing'
    };
    this.activeTasks.set(taskId, taskRecord);

    // 平行或串行處理
    let results: Array<{ agent: string; response: string; duration: number }>;

    if (parallel && agents.length > 1) {
      // 平行處理 - 同時呼叫多個 Agents
      const startTime = Date.now();
      const promises = agents.map(agent => this.callAgent(agent, task));
      const responses = await Promise.allSettled(promises);

      results = responses.map((result, i) => ({
        agent: agents[i].name,
        response: result.status === 'fulfilled' ? result.value : `Error: ${(result as PromiseRejectedResult).reason}`,
        duration: Date.now() - startTime
      }));
    } else {
      // 串行處理
      results = [];
      for (const agent of agents) {
        const startTime = Date.now();
        const response = await this.callAgent(agent, task);
        results.push({
          agent: agent.name,
          response,
          duration: Date.now() - startTime
        });
      }
    }

    // 如果有多個結果，進行整合
    let synthesis: string | null = null;
    if (results.length > 1) {
      synthesis = await this.synthesizeResults(task, results);
    }

    // 更新任務狀態
    taskRecord.status = 'completed';
    taskRecord.result = { results, synthesis };

    return {
      taskId,
      type,
      parallel,
      agentsUsed: agents.map(a => ({ id: a.id, name: a.name, role: a.role })),
      results,
      synthesis,
      totalDuration: Math.max(...results.map(r => r.duration))
    };
  }

  // 呼叫單一 Agent
  private async callAgent(agent: AIAgent, task: string): Promise<string> {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: agent.model,
        max_tokens: 2048,
        system: agent.systemPrompt,
        messages: [{ role: 'user', content: task }]
      })
    });

    if (!response.ok) {
      throw new Error(`Agent ${agent.name} error: ${response.status}`);
    }

    const data = await response.json() as { content: Array<{ text: string }> };
    return data.content[0]?.text || '';
  }

  // 整合多個 Agent 的結果
  private async synthesizeResults(task: string, results: Array<{ agent: string; response: string }>): Promise<string> {
    const synthesizer = AI_TEAM.find(a => a.id === 'synthesizer')!;

    const synthesisPrompt = `原始任務：${task}

以下是團隊成員的回應，請整合這些觀點：

${results.map(r => `【${r.agent}】\n${r.response}`).join('\n\n---\n\n')}

請整合以上觀點，提供：
1. 共識要點
2. 不同觀點的互補之處
3. 綜合建議`;

    return await this.callAgent(synthesizer, synthesisPrompt);
  }

  // 團隊共識討論
  async consensus(topic: string, rounds: number = 2): Promise<unknown> {
    const discussionHistory: Array<{ round: number; agent: string; contribution: string }> = [];

    // 每輪討論
    for (let round = 1; round <= rounds; round++) {
      const context = round === 1
        ? `討論議題：${topic}\n\n請分享你的觀點。`
        : `討論議題：${topic}\n\n前幾輪討論：\n${discussionHistory.map(d => `【${d.agent}】${d.contribution}`).join('\n')}\n\n請回應其他成員的觀點，並深化你的看法。`;

      // 這輪的參與者（輪流）
      const participants = AI_TEAM.filter(a => a.id !== 'synthesizer');

      for (const agent of participants) {
        const response = await this.callAgent(agent, context);
        discussionHistory.push({
          round,
          agent: agent.name,
          contribution: response
        });
      }
    }

    // 最終整合
    const synthesis = await this.synthesizeResults(topic, discussionHistory.map(d => ({
      agent: d.agent,
      response: d.contribution
    })));

    return {
      topic,
      rounds,
      discussion: discussionHistory,
      consensus: synthesis
    };
  }

  // 取得團隊狀態
  getStatus(taskId?: string): unknown {
    if (taskId) {
      return this.activeTasks.get(taskId) || { error: 'Task not found' };
    }

    return {
      team: AI_TEAM.map(a => ({
        id: a.id,
        name: a.name,
        role: a.role,
        specialty: a.specialty
      })),
      activeTasks: Array.from(this.activeTasks.values()),
      taskTypes: Object.keys(TASK_AGENT_MAPPING)
    };
  }
}

// MCP Server Handler
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    const coordinator = new TeamCoordinator(env);

    // Health check
    if (url.pathname === '/' || url.pathname === '/health') {
      return Response.json({
        status: 'healthy',
        service: 'particle-team-mcp',
        version: '1.0.0',
        team: AI_TEAM.map(a => ({ id: a.id, name: a.name, role: a.role })),
        capabilities: ['parallel_processing', 'team_consensus', 'agent_direct'],
        tools: TEAM_TOOLS.map(t => t.name)
      }, { headers: corsHeaders });
    }

    // MCP HTTP Endpoint
    if (url.pathname === '/mcp') {
      return this.handleMCP(request, env, coordinator, corsHeaders);
    }

    // SSE Endpoint
    if (url.pathname === '/sse') {
      return this.handleSSE(corsHeaders);
    }

    // Quick dispatch endpoint (非 MCP)
    if (url.pathname === '/dispatch' && request.method === 'POST') {
      const body = await request.json() as { task: string; type?: string; parallel?: boolean };
      const result = await coordinator.dispatch(body.task, body.type, body.parallel);
      return Response.json(result, { headers: corsHeaders });
    }

    return Response.json({ error: 'Not found' }, { status: 404, headers: corsHeaders });
  },

  async handleMCP(request: Request, env: Env, coordinator: TeamCoordinator, corsHeaders: Record<string, string>): Promise<Response> {
    if (request.method !== 'POST') {
      return Response.json({ error: 'Method not allowed' }, { status: 405, headers: corsHeaders });
    }

    const mcpRequest = await request.json() as { jsonrpc: string; id: number | string; method: string; params?: Record<string, unknown> };
    let response: unknown;

    switch (mcpRequest.method) {
      case 'initialize':
        response = {
          jsonrpc: '2.0',
          id: mcpRequest.id,
          result: {
            protocolVersion: '2024-11-05',
            serverInfo: { name: 'particle-team-mcp', version: '1.0.0' },
            capabilities: { tools: {} }
          }
        };
        break;

      case 'tools/list':
        response = {
          jsonrpc: '2.0',
          id: mcpRequest.id,
          result: { tools: TEAM_TOOLS }
        };
        break;

      case 'tools/call':
        response = await this.handleToolCall(mcpRequest, coordinator);
        break;

      default:
        response = {
          jsonrpc: '2.0',
          id: mcpRequest.id,
          error: { code: -32601, message: `Method not found: ${mcpRequest.method}` }
        };
    }

    return Response.json(response, { headers: corsHeaders });
  },

  async handleToolCall(mcpRequest: { id: number | string; params?: Record<string, unknown> }, coordinator: TeamCoordinator): Promise<unknown> {
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
            args.agents as string[] | undefined
          );
          break;

        case 'team_status':
          result = coordinator.getStatus(args.task_id as string | undefined);
          break;

        case 'agent_direct':
          const agent = AI_TEAM.find(a => a.id === args.agent_id);
          if (!agent) throw new Error(`Agent not found: ${args.agent_id}`);
          // 直接對話需要透過 dispatch 單一 agent
          result = await coordinator.dispatch(args.message as string, 'analyze', false, [args.agent_id as string]);
          break;

        case 'team_consensus':
          result = await coordinator.consensus(args.topic as string, (args.rounds as number) || 2);
          break;

        default:
          return {
            jsonrpc: '2.0',
            id: mcpRequest.id,
            error: { code: -32602, message: `Unknown tool: ${toolName}` }
          };
      }

      return {
        jsonrpc: '2.0',
        id: mcpRequest.id,
        result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
      };
    } catch (error) {
      return {
        jsonrpc: '2.0',
        id: mcpRequest.id,
        error: { code: -32603, message: error instanceof Error ? error.message : 'Internal error' }
      };
    }
  },

  handleSSE(corsHeaders: Record<string, string>): Response {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(`event: open\ndata: {"status":"connected","service":"particle-team-mcp"}\n\n`));
      }
    });

    return new Response(stream, {
      headers: {
        ...corsHeaders,
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache'
      }
    });
  }
};
