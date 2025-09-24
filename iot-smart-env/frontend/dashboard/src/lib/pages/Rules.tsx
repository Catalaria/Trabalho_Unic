import React from 'react'
import {
  listRules,
  createRule,
  updateRule,
  deleteRule,
  Rule,
  RuleIn,
  IS_MOCK,
} from '../api'

type Preset = { label: string; fill: Partial<RuleIn>; note?: string }

const PRESETS: Preset[] = [
  {
    label: 'Irrigação Matinal (solo ≤ 25%)',
    fill: {
      name: 'Irrigação Matinal',
      enabled: true,
      metric: 'soil_moisture_pct',
      operator: '<=',
      value: 25,
      action: 'irrigation_on',
      action_params: { zona: 'Jardim', duration_s: 20 },
    },
    note: 'Liga irrigação quando o solo estiver seco.',
  },
  {
    label: 'Alerta Umidade Alta (cozinha ≥ 75%)',
    fill: {
      name: 'Umidade Alta Cozinha',
      enabled: true,
      metric: 'humidity_pct',
      operator: '>=',
      value: 75,
      action: 'notify',
      action_params: { canal: 'push', area: 'cozinha' },
    },
    note: 'Evita mofo/condensação com aviso.',
  },
  {
    label: 'Temperatura Alta (sala ≥ 29°C)',
    fill: {
      name: 'Temp Alta Sala',
      enabled: false,
      metric: 'temperature_c',
      operator: '>=',
      value: 29,
      action: 'notify',
      action_params: { canal: 'email', area: 'sala' },
    },
    note: 'Sugerir ligar ar-condicionado (simulado).',
  },
]

function metricLabel(m: Rule['metric']) {
  return m === 'temperature_c'
    ? 'Temperatura (°C)'
    : m === 'humidity_pct'
    ? 'Umidade (%)'
    : 'Umidade do solo (%)'
}
function opLabel(o: Rule['operator']) {
  return o === '<=' ? '≤' : o === '>=' ? '≥' : o
}
function actionText(r: Rule) {
  if (r.action === 'irrigation_on') {
    const zona = (r.action_params as any)?.zona ?? 'Zona A'
    const dur = (r.action_params as any)?.duration_s ?? 15
    return `Irrigação (${zona}, ${dur}s)`
  }
  if (r.action === 'notify') {
    const canal = (r.action_params as any)?.canal ?? 'push'
    const area = (r.action_params as any)?.area
      ? ` — ${(r.action_params as any).area}`
      : ''
    return `Notificar (${canal}${area})`
  }
  return r.action
}

export default function RulesPage() {
  const [rules, setRules] = React.useState<Rule[]>([])
  const [loading, setLoading] = React.useState(false)
  const [form, setForm] = React.useState<RuleIn>({
    name: '',
    enabled: true,
    metric: 'soil_moisture_pct',
    operator: '<=',
    value: 25,
    action: 'irrigation_on',
    action_params: { zona: 'Jardim', duration_s: 20 },
  })

  const fetchData = async () => {
    setLoading(true)
    try {
      setRules(await listRules())
    } finally {
      setLoading(false)
    }
  }
  React.useEffect(() => {
    fetchData()
  }, [])

  const onPreset = (p: Preset) => setForm((f) => ({ ...f, ...p.fill }))

  const onCreate = async () => {
    try {
      const saved = await createRule(form)
      setRules((r) => [...r, saved])
      alert(IS_MOCK ? 'Regra criada (demo).' : 'Regra criada.')
    } catch (e: any) {
      alert(e.message || 'Falha ao criar regra.')
    }
  }

  const onDelete = async (id: number) => {
    if (!confirm('Excluir regra?')) return
    try {
      await deleteRule(id)
      setRules((r) => r.filter((x) => x.id !== id))
    } catch (e: any) {
      alert(e.message || 'Falha ao excluir.')
    }
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="mb-2 font-semibold">Regras</div>
        <div className="mb-2 flex items-center gap-8">
          <button className="btn-ghost" onClick={fetchData} disabled={loading}>
            {loading ? 'Atualizando...' : 'Atualizar'}
          </button>
          <div className="text-xs text-gray-500">
            {IS_MOCK
              ? 'Modo demo (mock): CRUD local.'
              : 'Para salvar no backend, use token admin.'}
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Nome</th>
                <th>Ativa</th>
                <th>Condição</th>
                <th>Ação</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rules.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '12px 0' }}>
                    Nenhuma regra
                  </td>
                </tr>
              ) : (
                rules.map((r) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td>{r.name}</td>
                    <td>
                      {r.enabled ? (
                        <span style={{ color: '#16a34a', fontWeight: 600 }}>
                          Sim
                        </span>
                      ) : (
                        <span style={{ color: '#6b7280' }}>Não</span>
                      )}
                    </td>
                    <td>
                      {metricLabel(r.metric)} {opLabel(r.operator)} {r.value}
                    </td>
                    <td>{actionText(r)}</td>
                    <td>
                      <button
                        className="btn-ghost"
                        onClick={() => onDelete(r.id)}
                      >
                        Excluir
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="mb-2 font-semibold">Nova regra</div>

        <div className="mb-2">
          <div className="label">Presets</div>
          <div
            className="grid"
            style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}
          >
            {PRESETS.map((p) => (
              <button
                key={p.label}
                className="btn-ghost"
                onClick={() => onPreset(p)}
                title={p.note}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div
          className="grid"
          style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}
        >
          <div>
            <div className="label">Nome</div>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <div className="label">Ativa</div>
            <select
              className="input"
              value={String(form.enabled)}
              onChange={(e) =>
                setForm({ ...form, enabled: e.target.value === 'true' })
              }
            >
              <option value="true">Sim</option>
              <option value="false">Não</option>
            </select>
          </div>
          <div>
            <div className="label">Métrica</div>
            <select
              className="input"
              value={form.metric}
              onChange={(e) =>
                setForm({ ...form, metric: e.target.value as any })
              }
            >
              <option value="temperature_c">Temperatura (°C)</option>
              <option value="humidity_pct">Umidade (%)</option>
              <option value="soil_moisture_pct">Umidade do solo (%)</option>
            </select>
          </div>
          <div>
            <div className="label">Operador</div>
            <select
              className="input"
              value={form.operator}
              onChange={(e) =>
                setForm({ ...form, operator: e.target.value as any })
              }
            >
              <option value="<">&lt;</option>
              <option value="<=">&le;</option>
              <option value=">">&gt;</option>
              <option value=">=">&ge;</option>
              <option value="==">==</option>
              <option value="!=">!=</option>
            </select>
          </div>
          <div>
            <div className="label">Valor</div>
            <input
              className="input"
              type="number"
              value={form.value}
              onChange={(e) =>
                setForm({ ...form, value: Number(e.target.value) })
              }
            />
          </div>
          <div>
            <div className="label">Ação</div>
            <select
              className="input"
              value={form.action}
              onChange={(e) =>
                setForm({ ...form, action: e.target.value as any })
              }
            >
              <option value="notify">Notificar</option>
              <option value="irrigation_on">Irrigação (simulada)</option>
            </select>
          </div>
          <div className="lg:col-span-3">
            <div className="label">Parâmetros (JSON)</div>
            <input
              className="input"
              value={JSON.stringify(form.action_params ?? {})}
              onChange={(e) => {
                try {
                  setForm({
                    ...form,
                    action_params: JSON.parse(e.target.value || '{}'),
                  })
                } catch {}
              }}
            />
          </div>
        </div>

        <div className="mt-3">
          <button className="btn-primary" onClick={onCreate}>
            Criar regra
          </button>
        </div>

        {!IS_MOCK && (
          <div className="mt-2 text-xs text-gray-500">
            Para salvar no backend real, use token admin.
          </div>
        )}
      </div>
    </div>
  )
}
