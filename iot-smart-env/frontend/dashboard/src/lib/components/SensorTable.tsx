import React from 'react'
import { listReadings, Reading } from '../api'

export default function SensorTable() {
  const [rows, setRows] = React.useState<Reading[]>([])
  const [node, setNode] = React.useState('')
  const [loading, setLoading] = React.useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const data = await listReadings({
        limit: 200,
        node_id: node || undefined,
      })
      setRows(data)
    } catch (e: any) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className="card">
      <div className="mb-2 font-semibold">Leituras (DB)</div>

      <div className="grid sm:grid-cols-3 lg:grid-cols-3">
        <div className="card">
          <div className="text-3xl font-bold">{rows.length}</div>
          <div className="text-sm text-gray-500">Amostras carregadas</div>
        </div>
        <div className="card">
          <div className="text-3xl font-bold">
            {new Set(rows.map((r) => r.node_id)).size}
          </div>
          <div className="text-sm text-gray-500">Nós distintos</div>
        </div>
        <div className="card">
          <div className="text-3xl font-bold">
            {rows.slice(-1)[0]?.temperature_c ?? '—'}
          </div>
          <div className="text-sm text-gray-500">Última Temp (°C)</div>
        </div>
      </div>

      <div
        className="mt-3 grid"
        style={{ gridTemplateColumns: '1fr auto', gap: '8px' }}
      >
        <div>
          <div className="label">Filtrar por Node ID</div>
          <input
            className="input"
            placeholder="ex.: sala"
            value={node}
            onChange={(e) => setNode(e.target.value)}
          />
        </div>
        <button className="btn-ghost" onClick={fetchData} disabled={loading}>
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      </div>

      <div className="mt-3" style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Horário</th>
              <th>Node</th>
              <th>Temp (°C)</th>
              <th>Umidade (%)</th>
              <th>Solo (%)</th>
              <th>Mov.</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '12px 0' }}>
                  Sem dados
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={`${r.id}-${r.timestamp}`}>
                  <td>{new Date(r.timestamp).toLocaleTimeString()}</td>
                  <td>{r.node_id}</td>
                  <td>{r.temperature_c ?? '—'}</td>
                  <td>{r.humidity_pct ?? '—'}</td>
                  <td>{r.soil_moisture_pct ?? '—'}</td>
                  <td>
                    <span style={{ color: '#6b7280' }}>
                      {r.motion ? 'Sim' : 'Não'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
