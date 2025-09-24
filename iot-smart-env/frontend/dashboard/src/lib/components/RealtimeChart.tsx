import React from 'react'
import { openRealtimeWS, Reading, listReadings } from '../api'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts'

type Props = { height?: number }

function FmtTooltip({ active, payload, label }: any) {
  if (!active || !payload || !payload.length) return null
  const time = (() => {
    try {
      return new Date(label).toLocaleTimeString()
    } catch {
      return label
    }
  })()
  const t = payload.find((p: any) => p.dataKey === 'temperature_c')?.value
  const h = payload.find((p: any) => p.dataKey === 'humidity_pct')?.value
  return (
    <div
      style={{
        background: 'var(--card)',
        color: 'var(--fg)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '8px 10px',
        boxShadow: '0 8px 24px rgba(0,0,0,.08)',
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>{time}</div>
      <div>Temp: {t == null ? '—' : `${Number(t).toFixed(1)} °C`}</div>
      <div>Umidade: {h == null ? '—' : `${Number(h).toFixed(0)} %`}</div>
    </div>
  )
}

export default function RealtimeChart({ height = 360 }: Props) {
  const [data, setData] = React.useState<Reading[]>([])
  const maxPoints = 240

  // 1) histórico inicial (evita "reset")
  React.useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const hist = await listReadings({ limit: 180 })
        if (mounted) setData(hist)
      } catch {}
    })()
    return () => {
      mounted = false
    }
  }, [])

  // 2) stream ao vivo
  React.useEffect(() => {
    const ws = openRealtimeWS()
    const onMessage = (ev: MessageEvent<string>) => {
      try {
        const msg: Reading = JSON.parse(ev.data)
        setData((prev) => {
          const next = [...prev, msg]
          if (next.length > maxPoints) next.splice(0, next.length - maxPoints)
          return next
        })
      } catch {}
    }
    ws.addEventListener('message', onMessage)

    const pingId: number = window.setInterval(() => {
      // @ts-ignore
      if (ws.readyState === WebSocket.OPEN) (ws as any).send?.('ping')
    }, 20_000)

    return () => {
      ws.removeEventListener('message', onMessage)
      window.clearInterval(pingId)
      try {
        ;(ws as any).close?.()
      } catch {}
    }
  }, [])

  const fmtTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString()
    } catch {
      return iso
    }
  }
  const nodes = React.useMemo(
    () => Array.from(new Set(data.map((d) => d.node_id))).join(', '),
    [data],
  )

  const tempDomain = React.useMemo<[number, number]>(() => {
    const vals = data
      .map((d) => d.temperature_c)
      .filter((v): v is number => typeof v === 'number')
    if (!vals.length) return [0, 50]
    const min = Math.min(...vals)
    const max = Math.max(...vals)
    const pad = Math.max(1, (max - min) * 0.15)
    return [Math.floor(min - pad), Math.ceil(max + pad)]
  }, [data])

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <div className="font-semibold">Tempo real</div>
          <div className="text-xs text-gray-500">Nó(s): {nodes || '—'}</div>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="mt-6 text-sm text-gray-500">
          Aguardando dados em tempo real…
        </div>
      ) : (
        <div style={{ width: '100%', height }}>
          <ResponsiveContainer>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={fmtTime}
                minTickGap={24}
              />
              <YAxis yAxisId="temp" domain={tempDomain} />
              <YAxis yAxisId="hum" orientation="right" domain={[0, 100]} />
              <Tooltip content={<FmtTooltip />} />
              <Legend />
              <ReferenceLine y={0} yAxisId="temp" strokeDasharray="3 3" />
              <ReferenceLine y={100} yAxisId="hum" strokeDasharray="3 3" />
              <Line
                yAxisId="temp"
                type="monotone"
                dataKey="temperature_c"
                name="Temp (°C)"
                dot={false}
                strokeWidth={2}
                isAnimationActive={false}
                stroke="#ef4444" /* vermelho */
              />
              <Line
                yAxisId="hum"
                type="monotone"
                dataKey="humidity_pct"
                name="Umidade (%)"
                dot={false}
                strokeWidth={2}
                isAnimationActive={false}
                stroke="#3b82f6" /* azul */
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-2 text-xs text-gray-500">
        Mostrando últimas {Math.min(data.length, maxPoints)} amostras
      </div>
    </div>
  )
}
