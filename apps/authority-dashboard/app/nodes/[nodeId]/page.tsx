'use client'

// Node Details Page - Individual node telemetry and assessments

import { useEffect, useState } from 'react'
import { GlassPanel } from '@/components/ui/GlassPanel'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { api } from '@/lib/api'
import { formatTimestamp, getTimeSince, formatValue, getSeverityColor } from '@/lib/utils'
import type { Node, TelemetryRecord, SensorAssessment, HazardAssessment } from '@/types'

export default function NodeDetailsPage({ params }: { params: { nodeId: string } }) {
  const [node, setNode] = useState<Node | null>(null)
  const [telemetry, setTelemetry] = useState<TelemetryRecord[]>([])
  const [sensorAssessments, setSensorAssessments] = useState<SensorAssessment[]>([])
  const [hazardAssessments, setHazardAssessments] = useState<HazardAssessment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  const fetchNodeData = async () => {
    try {
      setError(null)
      const [nodeData, telemetryData, sensorsData, hazardsData] = await Promise.all([
        api.getNode(params.nodeId),
        api.getNodeTelemetry(params.nodeId, 10),
        api.getNodeSensorAssessments(params.nodeId),
        api.getNodeHazardAssessments(params.nodeId),
      ])

      setNode(nodeData)
      setTelemetry(telemetryData)
      setSensorAssessments(sensorsData)
      setHazardAssessments(hazardsData)
      setLastUpdate(formatTimestamp(new Date().toISOString()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load node data')
      console.error('Node data fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNodeData()
    const interval = setInterval(fetchNodeData, 10000)
    return () => clearInterval(interval)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.nodeId])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !node) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
        <ErrorState title="Node Error" message={error || 'Node not found'} onRetry={fetchNodeData} />
      </div>
    )
  }

  const latestTelemetry = telemetry[0]
  const activeHazards = hazardAssessments.filter(h => h.state && !['NORMAL', 'RESOLVED'].includes(h.state))

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <SectionHeader
          title={node.node_id}
          subtitle={`Updated ${lastUpdate}`}
          action={<StatusBadge status={node.status} variant="node" size="md" />}
        />

        {/* Node Info */}
        <GlassPanel className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {node.location && (
              <div>
                <div className="text-xs text-zinc-500 mb-1">Location</div>
                <div className="text-sm font-mono text-zinc-300">
                  {node.location.lat.toFixed(6)}, {node.location.lon.toFixed(6)}
                </div>
              </div>
            )}
            {node.last_telemetry_at && (
              <div>
                <div className="text-xs text-zinc-500 mb-1">Last Telemetry</div>
                <div className="text-sm text-zinc-300">
                  {getTimeSince(node.last_telemetry_at)}
                </div>
              </div>
            )}
            {node.battery_pct != null && (
              <div>
                <div className="text-xs text-zinc-500 mb-1">Battery</div>
                <div className="text-sm font-semibold text-zinc-300">
                  {node.battery_pct}%
                </div>
              </div>
            )}
          </div>
        </GlassPanel>

        {/* Active Hazards Alert */}
        {activeHazards.length > 0 && (
          <GlassPanel className="mb-6 border-red-500/20">
            <h3 className="text-lg font-semibold text-red-300 mb-3">Active Hazards</h3>
            <div className="space-y-2">
              {activeHazards.map((hazard) => (
                <div key={hazard.assessment_id} className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-zinc-100 uppercase">{hazard.hazard_type}</span>
                    {hazard.severity != null && (
                      <span className={`ml-3 text-sm ${getSeverityColor(hazard.severity)}`}>
                        Severity: {(hazard.severity * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <StatusBadge status={hazard.state || 'UNKNOWN'} variant="hazard" size="sm" />
                </div>
              ))}
            </div>
          </GlassPanel>
        )}

        {/* Latest Telemetry */}
        {latestTelemetry && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-zinc-100 mb-4">Latest Telemetry</h3>
            <GlassPanel>
              <div className="mb-4">
                <div className="text-xs text-zinc-500">Measured</div>
                <div className="text-sm text-zinc-300">
                  {formatTimestamp(latestTelemetry.measurement_timestamp)}
                  <span className="mx-2">•</span>
                  {getTimeSince(latestTelemetry.measurement_timestamp)}
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {latestTelemetry.measurements.temp_c != null && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-zinc-500 mb-1">Temperature</div>
                    <div className="text-xl font-bold text-zinc-100">
                      {formatValue(latestTelemetry.measurements.temp_c, 1)}°C
                    </div>
                  </div>
                )}
                {latestTelemetry.measurements.humidity_pct != null && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-zinc-500 mb-1">Humidity</div>
                    <div className="text-xl font-bold text-zinc-100">
                      {formatValue(latestTelemetry.measurements.humidity_pct, 1)}%
                    </div>
                  </div>
                )}
                {latestTelemetry.measurements.pressure_hpa != null && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-zinc-500 mb-1">Pressure</div>
                    <div className="text-xl font-bold text-zinc-100">
                      {formatValue(latestTelemetry.measurements.pressure_hpa, 1)} hPa
                    </div>
                  </div>
                )}
                {latestTelemetry.measurements.gas_adc != null && (
                  <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-xs text-zinc-500 mb-1">Gas (ADC)</div>
                    <div className="text-xl font-bold text-zinc-100">
                      {formatValue(latestTelemetry.measurements.gas_adc, 0)}
                    </div>
                  </div>
                )}
              </div>

              {latestTelemetry.measurements.vibration_mps2 != null && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <div className="bg-white/5 rounded-lg p-3 inline-block">
                    <div className="text-xs text-zinc-500 mb-1">Vibration (MPU6500)</div>
                    <div className="text-xl font-bold text-zinc-100">
                      {formatValue(latestTelemetry.measurements.vibration_mps2, 2)} m/s²
                    </div>
                  </div>
                </div>
              )}

              {latestTelemetry.power && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <div className="grid grid-cols-2 gap-4">
                    {latestTelemetry.power.battery_pct != null && (
                      <div>
                        <div className="text-xs text-zinc-500">Battery</div>
                        <div className="text-lg font-semibold text-zinc-100">
                          {formatValue(latestTelemetry.power.battery_pct, 0)}%
                        </div>
                      </div>
                    )}
                    {latestTelemetry.power.voltage_mv != null && (
                      <div>
                        <div className="text-xs text-zinc-500">Voltage</div>
                        <div className="text-lg font-semibold text-zinc-100">
                          {formatValue(latestTelemetry.power.voltage_mv, 0)} mV
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </GlassPanel>
          </div>
        )}

        {/* Sensor Assessments */}
        {sensorAssessments.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-zinc-100 mb-4">Sensor Health</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sensorAssessments.slice(0, 6).map((assessment) => (
                <GlassPanel key={assessment.assessment_id}>
                  <div className="text-sm font-semibold text-zinc-300 mb-3">
                    {assessment.sensor_type}
                  </div>
                  <div className="space-y-2 text-sm">
                    {assessment.health != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Health:</span>
                        <span className="text-zinc-100">{(assessment.health * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    {assessment.quality != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Quality:</span>
                        <span className="text-zinc-100">{(assessment.quality * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    {assessment.reliability != null && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Reliability:</span>
                        <span className="text-zinc-100">{(assessment.reliability * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    {assessment.baseline_state && (
                      <div className="flex justify-between">
                        <span className="text-zinc-500">Baseline:</span>
                        <span className="text-zinc-100">{assessment.baseline_state}</span>
                      </div>
                    )}
                  </div>
                </GlassPanel>
              ))}
            </div>
          </div>
        )}

        {/* Telemetry History */}
        {telemetry.length > 1 && (
          <div>
            <h3 className="text-xl font-semibold text-zinc-100 mb-4">Recent Telemetry</h3>
            <div className="space-y-3">
              {telemetry.slice(1, 10).map((record) => (
                <GlassPanel key={record.telemetry_id} className="flex items-center justify-between">
                  <div>
                    <div className="text-sm text-zinc-300">
                      {formatTimestamp(record.measurement_timestamp)}
                    </div>
                    <div className="text-xs text-zinc-500 mt-1">
                      {record.measurements.temp_c != null && `${formatValue(record.measurements.temp_c, 1)}°C`}
                      {record.measurements.humidity_pct != null && ` • ${formatValue(record.measurements.humidity_pct, 1)}% RH`}
                    </div>
                  </div>
                  <div className="text-xs text-zinc-600">
                    {getTimeSince(record.measurement_timestamp)}
                  </div>
                </GlassPanel>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
