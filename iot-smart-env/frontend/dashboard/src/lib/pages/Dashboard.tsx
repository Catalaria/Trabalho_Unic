import React from 'react'
import { getHealth } from '../api'
import MetricCard from '../components/MetricCard'
import RealtimeChart from '../components/RealtimeChart'
import SensorTable from '../components/SensorTable'

export default function Dashboard() {
  const [health, setHealth] = React.useState<Awaited<
    ReturnType<typeof getHealth>
  > | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    ;(async () => {
      try {
        const h = await getHealth()
        setHealth(h)
      } catch (e: any) {
        setError(e.message || 'Falha ao consultar /health')
      }
    })()
  }, [])

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label="Status"
          value={health?.status ?? '—'}
          hint={health ? 'EDGE operacional' : error ?? '—'}
        />
        <MetricCard
          label="Leituras (DB)"
          value={health?.counts.readings ?? '—'}
        />
        <MetricCard label="Nós distintos" value={health?.counts.nodes ?? '—'} />
      </div>

      <RealtimeChart />

      <SensorTable limit={200} />
    </div>
  )
}
