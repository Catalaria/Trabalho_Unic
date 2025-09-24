import React from 'react'

type Props = {
  label: string
  value: string | number
  hint?: string
}

export default function MetricCard({ label, value, hint }: Props) {
  return (
    <div className="card p-4">
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
      {hint && <div className="text-xs text-gray-500 mt-1">{hint}</div>}
    </div>
  )
}
