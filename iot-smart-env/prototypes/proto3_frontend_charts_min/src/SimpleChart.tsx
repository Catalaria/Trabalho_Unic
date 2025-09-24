import React from 'react'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

type Reading = {
  id: number
  node_id: string
  temperature_c?: number | null
  humidity_pct?: number | null
  soil_moisture_pct?: number | null
  motion?: boolean | null
  timestamp: string
}

export default function SimpleChart() {
  const [data, setData] = React.useState<Reading[]>([])
  const maxPoints = 120

  React.useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws')
    ws.onmessage = (ev) => {
      try {
        const msg: Reading = JSON.parse(ev.data)
        setData((prev) => {
          const next = [...prev, msg]
          if (next.length > maxPoints) next.shift()
          return next
        })
      } catch {}
    }
    ws.onopen = () => {
      // Mantém a conexão viva
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      }, 20000)
      ;(ws as any).__ping = ping
    }
    ws.onclose = () => {
      const ping = (ws as any).__ping
      if (ping) clearInterval(ping)
    }
    return () => {
      try {
        ws.close()
      } catch {}
    }
  }, [])

  const fmtTime = (iso: string) => {
    try {
      const d = new Date(iso)
      return d.toLocaleTimeString()
    } catch {
      return iso
    }
  }

  const nodes = React.useMemo(
    () => Array.from(new Set(data.map((d) => d.node_id))).join(', '),
    [data],
  )

  return (
    <div style={{ width: '100%', height: 420 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" tickFormatter={fmtTime} minTickGap={24} />
          <YAxis yAxisId="temp" domain={[0, 50]} />
          <YAxis yAxisId="hum" orientation="right" domain={[0, 100]} />
          <Tooltip labelFormatter={fmtTime} />
          <Legend />
          <Line
            yAxisId="temp"
            type="monotone"
            dataKey="temperature_c"
            name="Temp (°C)"
            dot={false}
          />
          <Line
            yAxisId="hum"
            type="monotone"
            dataKey="humidity_pct"
            name="Umidade (%)"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
        Mostrando últimas {Math.min(data.length, maxPoints)} leituras — node(s):{' '}
        {nodes || '—'}
      </p>
    </div>
  )
}
