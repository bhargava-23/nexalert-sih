'use client'

// Live Monitoring Page - Real-time telemetry and sensor data

import { useEffect, useState } from 'react'
import { GlassPanel } from '@/components/ui/GlassPanel'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { api } from '@/lib/api'
import { formatTimestamp, getTimeSince, formatValue } from '@/lib/utils'
import type { TelemetryRecord } from '@/types'

export default function MonitoringPage() {
  const [telemetry, setTelemetry] = useState<TelemetryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  const fetchTelemetry = async () => {
    try {
      setError(null)
      const data = await api.getLatestTelemetry()
      setTelemetry(data)
      setLastUpdate(formatTimestamp(new Date().toISOString()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load telemetry')
      console.error('Telemetry fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTelemetry()
    const interval = setInterval(fetchTelemetry, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
        <ErrorState title="Monitoring Error" message={error} onRetry={fetchTelemetry} />
      </div>
    )
  }

  const getDataAge = (timestamp: string) => {
    const age = Date.now() - new Date(timestamp).getTime()
    const seconds = Math.floor(age / 1000)
    return seconds > 60 ? 'stale' : 'live'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <SectionHeader
          title="Live Monitoring"
          subtitle={`${telemetry.length} telemetry records • Updated ${lastUpdate}`}
        />

        {telemetry.length === 0 ? (
          <GlassPanel className="text-center py-12">
            <p className="text-zinc-400">No telemetry data available</p>
          </GlassPanel>
        ) : (
          <div className="space-y-6">
            {telemetry.map((record) => {
              const dataAge = getDataAge(record.measurement_timestamp)
              return (
                <GlassPanel key={record.telemetry_id}>
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-zinc-100 text-lg">{record.node_id}</h3>
                      <p className="text-sm text-zinc-500">
                        Measured: {formatTimestamp(record.measurement_timestamp)}
                        <span className="mx-2">•</span>
                        {getTimeSince(record.measurement_timestamp)}
                      </p>
                    </div>
                    <StatusBadge
                      status={dataAge === 'stale' ? 'STALE' : 'LIVE'}
                      variant="info"
                      size="sm"
                    />
                  </div>

                  {/* BME680 Environmental Sensors */}
                  <div className="mb-6">
                    <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-3">
                      BME680 Environmental
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {record.measurements.temp_c != null && (
                        <div className="bg-white/5 rounded-lg p-3">
                          <div className="text-xs text-zinc-500 mb-1">Temperature</div>
                          <div className="text-2xl font-bold text-zinc-100">
                            {formatValue(record.measurements.temp_c, 1)}°C
                          </div>
                        </div>
                      )}
                      {record.measurements.humidity_pct != null && (
                        <div className="bg-white/5 rounded-lg p-3">
                          <div className="text-xs text-zinc-500 mb-1">Humidity</div>
                          <div className="text-2xl font-bold text-zinc-100">
                            {formatValue(record.measurements.humidity_pct, 1)}%
                          </div>
                        </div>
                      )}
                      {record.measurements.pressure_hpa != null && (
                        <div className="bg-white/5 rounded-lg p-3">
                          <div className="text-xs text-zinc-500 mb-1">Pressure</div>
                          <div className="text-2xl font-bold text-zinc-100">
                            {formatValue(record.measurements.pressure_hpa, 1)} hPa
                          </div>
                        </div>
                      )}
                      {record.measurements.gas_adc != null && (
                        <div className="bg-white/5 rounded-lg p-3">
                          <div className="text-xs text-zinc-500 mb-1">Gas (ADC)</div>
                          <div className="text-2xl font-bold text-zinc-100">
                            {formatValue(record.measurements.gas_adc, 0)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* MPU6500 Motion/Vibration */}
                  {record.measurements.vibration_mps2 != null && (
                    <div className="mb-6">
                      <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-3">
                        MPU6500 Motion
                      </h4>
                      <div className="bg-white/5 rounded-lg p-3 inline-block">
                        <div className="text-xs text-zinc-500 mb-1">Vibration</div>
                        <div className="text-2xl font-bold text-zinc-100">
                          {formatValue(record.measurements.vibration_mps2, 2)} m/s²
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Power Status */}
                  {record.power && (
                    <div className="border-t border-white/10 pt-4">
                      <h4 className="text-sm font-semibold text-zinc-400 uppercase tracking-wide mb-3">
                        Power
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        {record.power.battery_pct != null && (
                          <div>
                            <div className="text-xs text-zinc-500">Battery</div>
                            <div className="text-lg font-semibold text-zinc-100">
                              {formatValue(record.power.battery_pct, 0)}%
                            </div>
                          </div>
                        )}
                        {record.power.voltage_mv != null && (
                          <div>
                            <div className="text-xs text-zinc-500">Voltage</div>
                            <div className="text-lg font-semibold text-zinc-100">
                              {formatValue(record.power.voltage_mv, 0)} mV
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Location */}
                  {record.location && (
                    <div className="border-t border-white/10 pt-4 mt-4">
                      <div className="text-xs text-zinc-500">Location</div>
                      <div className="text-sm font-mono text-zinc-400">
                        {record.location.lat.toFixed(6)}, {record.location.lon.toFixed(6)}
                        {record.location.alt != null && ` @ ${formatValue(record.location.alt, 0)}m`}
                      </div>
                    </div>
                  )}
                </GlassPanel>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
