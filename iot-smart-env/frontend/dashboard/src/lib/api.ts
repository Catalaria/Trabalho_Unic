/* API + MOCK (suave por random walk)
   - VITE_API_URL: base da API (padrão http://localhost:8000)
   - VITE_USE_MOCK: "1" (default) usa mock. Coloque "0" para usar backend real.
*/
export type Health = {
  status: string
  mqtt: { host: string; port: number; topic: string }
  counts: { readings: number; nodes: number }
  db_url: string
}
export type Reading = {
  id?: number
  node_id: string
  temperature_c?: number | null
  humidity_pct?: number | null
  soil_moisture_pct?: number | null
  motion?: boolean | null
  timestamp: string
}
export type Rule = {
  id: number
  name: string
  enabled: boolean
  metric: 'temperature_c' | 'humidity_pct' | 'soil_moisture_pct'
  operator: '<' | '<=' | '>' | '>=' | '==' | '!='
  value: number
  action: 'notify' | 'irrigation_on'
  action_params?: Record<string, unknown> | null
  created_at?: string
  updated_at?: string
}
export type RuleIn = Omit<Rule, 'id' | 'created_at' | 'updated_at'>

const BASE =
  (import.meta as any).env?.VITE_API_URL?.replace(/\/+$/, '') ||
  `${location.protocol}//${location.hostname}${
    location.port ? ':' + location.port : ''
  }`

export const IS_MOCK: boolean =
  ((import.meta as any).env?.VITE_USE_MOCK ?? '1') === '1'

/* ---------------- MOCK state: random walk por nó ---------------- */
type NodeState = { t: number; h: number; s: number }
type MockState = {
  seqId: number
  readings: Reading[]
  nodes: string[]
  nodeState: Record<string, NodeState>
  rules: Rule[]
}
const mock: MockState = {
  seqId: 1,
  readings: [],
  nodes: ['sala', 'cozinha', 'jardim'],
  nodeState: {},
  rules: [
    {
      id: 1,
      name: 'Irrigação Matinal (solo <= 25%)',
      enabled: true,
      metric: 'soil_moisture_pct',
      operator: '<=',
      value: 25,
      action: 'irrigation_on',
      action_params: { zona: 'Jardim', duration_s: 20 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 2,
      name: 'Alerta de Umidade Alta na Cozinha (>= 75%)',
      enabled: true,
      metric: 'humidity_pct',
      operator: '>=',
      value: 75,
      action: 'notify',
      action_params: { canal: 'push', area: 'cozinha' },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 3,
      name: 'Temperatura Alta na Sala (>= 29°C)',
      enabled: false,
      metric: 'temperature_c',
      operator: '>=',
      value: 29,
      action: 'notify',
      action_params: { canal: 'email', area: 'sala' },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
}

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n))
}
function rnd(delta: number) {
  return (Math.random() * 2 - 1) * delta
}

function ensureNodeState(id: string): NodeState {
  if (!mock.nodeState[id]) {
    // bases por ambiente
    const baseT = id === 'cozinha' ? 25 : id === 'sala' ? 24 : 23
    const baseH = id === 'cozinha' ? 65 : id === 'sala' ? 55 : 50
    const baseS = id === 'jardim' ? 35 : 20
    mock.nodeState[id] = { t: baseT, h: baseH, s: baseS }
  }
  return mock.nodeState[id]
}

function stepReading(node_id?: string): Reading {
  const id =
    node_id || mock.nodes[Math.floor(Math.random() * mock.nodes.length)]
  const st = ensureNodeState(id)
  // random walk suave
  st.t = clamp(st.t + rnd(0.2), 17, 35)
  st.h = clamp(st.h + rnd(2.5), 30, 90)
  st.s = clamp(st.s + rnd(3.0), 5, 95)
  const motion = Math.random() < 0.05

  const r: Reading = {
    id: mock.seqId++,
    node_id: id,
    temperature_c: Number(st.t.toFixed(1)),
    humidity_pct: Math.round(st.h),
    soil_moisture_pct: Math.round(st.s),
    motion,
    timestamp: new Date().toISOString(),
  }
  return r
}

function seedMockReadings(n = 120) {
  const now = Date.now()
  const stepMs = 10_000 // 10s
  for (let i = n - 1; i >= 0; i--) {
    const r = stepReading()
    r.timestamp = new Date(now - i * stepMs).toISOString()
    mock.readings.push(r)
  }
}
if (IS_MOCK && mock.readings.length === 0) seedMockReadings(180)

// Mock WS: 1 frame/1.5s
class MockWS {
  readyState = 1
  private timer: number | null = null
  private listeners = new Set<(ev: MessageEvent<string>) => void>()
  addEventListener(type: 'message', fn: (ev: MessageEvent<string>) => void) {
    if (type !== 'message') return
    this.listeners.add(fn)
    if (!this.timer) {
      this.timer = window.setInterval(() => {
        const r = stepReading()
        mock.readings.push(r)
        const ev = { data: JSON.stringify(r) } as MessageEvent<string>
        this.listeners.forEach((l) => l(ev))
      }, 1500)
    }
  }
  removeEventListener(_t: 'message', fn: (ev: MessageEvent<string>) => void) {
    this.listeners.delete(fn)
    if (this.listeners.size === 0 && this.timer) {
      window.clearInterval(this.timer)
      this.timer = null
    }
  }
  send(_d: string) {}
  close() {
    if (this.timer) window.clearInterval(this.timer)
    this.timer = null
    this.readyState = 3
    this.listeners.clear()
  }
}

/* ---------------- HTTP helpers ---------------- */
async function tryTwo<T>(
  pathA: string,
  pathB: string,
  init?: RequestInit,
): Promise<T> {
  let res = await fetch(`${BASE}${pathA}`, init)
  if (res.status === 404) res = await fetch(`${BASE}${pathB}`, init)
  if (!res.ok)
    throw new Error(
      (await res.text().catch(() => '')) || `${res.status} ${res.statusText}`,
    )
  return res.json()
}
const TOKEN_KEY = 'edge_admin_token'
export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
function authHeaders(): Record<string, string> {
  const t = getToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

/* ---------------- Endpoints (mock-aware) ---------------- */
export async function getHealth(): Promise<Health> {
  if (IS_MOCK) {
    return {
      status: 'ok',
      mqtt: { host: 'mock', port: 1883, topic: 'iot/mock/+' },
      counts: {
        readings: mock.readings.length,
        nodes: new Set(mock.readings.map((r) => r.node_id)).size,
      },
      db_url: 'sqlite:///./edge_readings.db',
    }
  }
  return tryTwo<Health>('/health', '/api/health')
}

type ListReadingsParams = {
  limit?: number
  node_id?: string
  since?: string
  until?: string
}
export async function listReadings(
  params: ListReadingsParams = {},
): Promise<Reading[]> {
  if (IS_MOCK) {
    let items = [...mock.readings]
    if (params.node_id)
      items = items.filter((r) => r.node_id === params.node_id)
    if (params.since) items = items.filter((r) => r.timestamp >= params.since!)
    if (params.until) items = items.filter((r) => r.timestamp <= params.until!)
    if (params.limit != null) items = items.slice(-params.limit)
    return items
  }
  const q = new URLSearchParams()
  if (params.limit != null) q.set('limit', String(params.limit))
  if (params.node_id) q.set('node_id', params.node_id)
  if (params.since) q.set('since', params.since)
  if (params.until) q.set('until', params.until)
  return tryTwo<Reading[]>(`/readings?${q}`, `/api/readings?${q}`)
}

export async function listRules(): Promise<Rule[]> {
  if (IS_MOCK) return [...mock.rules]
  return tryTwo<Rule[]>('/rules', '/api/rules')
}
export async function createRule(body: RuleIn): Promise<Rule> {
  if (IS_MOCK) {
    const r: Rule = {
      id: mock.rules.length ? Math.max(...mock.rules.map((x) => x.id)) + 1 : 1,
      ...body,
      action_params: body.action_params ?? {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    mock.rules.push(r)
    return r
  }
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...authHeaders(),
  }
  return tryTwo<Rule>('/rules', '/api/rules', {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
}
export async function updateRule(id: number, body: RuleIn): Promise<Rule> {
  if (IS_MOCK) {
    const i = mock.rules.findIndex((r) => r.id === id)
    if (i < 0) throw new Error('Regra não encontrada (mock)')
    mock.rules[i] = {
      ...mock.rules[i],
      ...body,
      updated_at: new Date().toISOString(),
    }
    return mock.rules[i]
  }
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...authHeaders(),
  }
  return tryTwo<Rule>(`/rules/${id}`, `/api/rules/${id}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(body),
  })
}
export async function deleteRule(id: number): Promise<{ ok: true }> {
  if (IS_MOCK) {
    const i = mock.rules.findIndex((r) => r.id === id)
    if (i >= 0) mock.rules.splice(i, 1)
    return { ok: true }
  }
  const headers: HeadersInit = { ...authHeaders() }
  return tryTwo<{ ok: true }>(`/rules/${id}`, `/api/rules/${id}`, {
    method: 'DELETE',
    headers,
  })
}

/* ---------------- WebSocket (mock-aware) ---------------- */
export function openRealtimeWS(): WebSocket {
  if (IS_MOCK) return new MockWS() as unknown as WebSocket
  const http = BASE.startsWith('https') ? 'wss' : 'ws'
  const baseUrl = new URL(BASE)
  const host = baseUrl.hostname
  const port = baseUrl.port || (http === 'wss' ? '443' : '80')
  return new WebSocket(`${http}://${host}:${port}/ws/realtime`)
}

/* utils para UI */
export function addDemoBurst(n = 20) {
  for (let i = 0; i < n; i++) mock.readings.push(stepReading())
}
export function mockNodes(): string[] {
  return [...new Set(mock.readings.map((r) => r.node_id))]
}
