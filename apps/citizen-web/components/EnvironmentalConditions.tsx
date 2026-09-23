'use client'

// Environmental conditions display - real telemetry data only

import { GlassCard } from '@/components/ui/GlassCard'
import type { TelemetryRecord } from '@/types'

interface EnvironmentalConditionsProps {
  telemetry: TelemetryRecord[]
}

export function EnvironmentalConditions({ telemetry }: EnvironmentalConditionsProps) {
  if (telemetry.length === 0) return null

  const latest = telemetry[0]
  const measurements = latest.measurements

  if (!measurements) return null

  const conditions = []

  if (measurements.temp_c != null) {
    conditions.push({
      label: 'Temperature',
      value: `${measurements.temp_c.toFixed(1)}°C`,
    })
  }

  if (measurements.humidity_pct != null) {
    conditions.push({
      label: 'Humidity',
      value: `${measurements.humidity_pct.toFixed(1)}%`,
    })
  }

  if (measurements.pressure_hpa != null) {
    conditions.push({
      label: 'Pressure',
      value: `${measurements.pressure_hpa.toFixed(0)} hPa`,
    })
  }

  if (conditions.length === 0) return null

  return (
    <GlassCard>
      <h3 className="font-semibold text-zinc-100 mb-3 flex items-center gap-2">
        <span>🌡️</span>
        <span>Environmental Conditions</span>
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {conditions.map((condition) => (
          <div key={condition.label} className="bg-zinc-800/50 rounded-xl p-3">
            <p className="text-xs text-zinc-500 mb-1">{condition.label}</p>
            <p className="text-xl font-bold text-zinc-100">{condition.value}</p>
          </div>
        ))}
      </div>
      <p className="text-xs text-zinc-600 mt-3">
        Data from NexAlert monitoring network
      </p>
    </GlassCard>
  )
}
