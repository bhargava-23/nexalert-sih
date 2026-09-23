'use client'

// Hazards Page - Hazard assessment list and details

import { useEffect, useState } from 'react'
import { GlassPanel } from '@/components/ui/GlassPanel'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { api } from '@/lib/api'
import { formatTimestamp, getTimeSince, getSeverityColor } from '@/lib/utils'
import type { HazardAssessment } from '@/types'

export default function HazardsPage() {
  const [hazards, setHazards] = useState<HazardAssessment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  const fetchHazards = async () => {
    try {
      setError(null)
      const data = await api.getGlobalHazards()
      setHazards(data)
      setLastUpdate(formatTimestamp(new Date().toISOString()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load hazards')
      console.error('Hazards fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHazards()
    const interval = setInterval(fetchHazards, 10000)
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
        <ErrorState title="Hazards Error" message={error} onRetry={fetchHazards} />
      </div>
    )
  }

  const activeHazards = hazards.filter(h => h.state && !['NORMAL', 'RESOLVED'].includes(h.state))
  const resolvedHazards = hazards.filter(h => h.state === 'RESOLVED')

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <SectionHeader
          title="Hazard Assessments"
          subtitle={`${activeHazards.length} active, ${resolvedHazards.length} resolved • Updated ${lastUpdate}`}
        />

        {hazards.length === 0 ? (
          <GlassPanel className="text-center py-12">
            <div className="text-4xl mb-4">✓</div>
            <p className="text-zinc-400">No hazard assessments</p>
          </GlassPanel>
        ) : (
          <>
            {/* Active Hazards */}
            {activeHazards.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-zinc-100 mb-4">Active Hazards</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {activeHazards.map((hazard) => (
                    <GlassPanel key={hazard.assessment_id}>
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h4 className="font-semibold text-zinc-100 text-lg uppercase">
                            {hazard.hazard_type}
                          </h4>
                          <p className="text-xs text-zinc-500 mt-1">
                            Detected {getTimeSince(hazard.created_at)}
                          </p>
                        </div>
                        {hazard.state && (
                          <StatusBadge status={hazard.state} variant="hazard" size="md" />
                        )}
                      </div>

                      <div className="space-y-3">
                        {hazard.evidence != null && (
                          <div>
                            <div className="text-xs text-zinc-500 mb-1">Evidence</div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${getSeverityColor(hazard.evidence)} bg-current`}
                                  style={{ width: `${hazard.evidence * 100}%` }}
                                />
                              </div>
                              <div className={`text-sm font-semibold ${getSeverityColor(hazard.evidence)}`}>
                                {(hazard.evidence * 100).toFixed(0)}%
                              </div>
                            </div>
                          </div>
                        )}

                        {hazard.confidence != null && (
                          <div>
                            <div className="text-xs text-zinc-500 mb-1">Confidence</div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${getSeverityColor(hazard.confidence)} bg-current`}
                                  style={{ width: `${hazard.confidence * 100}%` }}
                                />
                              </div>
                              <div className={`text-sm font-semibold ${getSeverityColor(hazard.confidence)}`}>
                                {(hazard.confidence * 100).toFixed(0)}%
                              </div>
                            </div>
                          </div>
                        )}

                        {hazard.severity != null && (
                          <div>
                            <div className="text-xs text-zinc-500 mb-1">Severity</div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${getSeverityColor(hazard.severity)} bg-current`}
                                  style={{ width: `${hazard.severity * 100}%` }}
                                />
                              </div>
                              <div className={`text-sm font-semibold ${getSeverityColor(hazard.severity)}`}>
                                {(hazard.severity * 100).toFixed(0)}%
                              </div>
                            </div>
                          </div>
                        )}

                        {hazard.risk != null && (
                          <div>
                            <div className="text-xs text-zinc-500 mb-1">Operational Risk</div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${getSeverityColor(hazard.risk)} bg-current`}
                                  style={{ width: `${hazard.risk * 100}%` }}
                                />
                              </div>
                              <div className={`text-sm font-semibold ${getSeverityColor(hazard.risk)}`}>
                                {(hazard.risk * 100).toFixed(0)}%
                              </div>
                            </div>
                          </div>
                        )}

                        {hazard.information_condition && (
                          <div className="border-t border-white/10 pt-3">
                            <div className="text-xs text-zinc-500">Information Quality</div>
                            <div className="text-sm font-medium text-zinc-300 mt-1">
                              {hazard.information_condition}
                            </div>
                          </div>
                        )}
                      </div>
                    </GlassPanel>
                  ))}
                </div>
              </div>
            )}

            {/* Resolved Hazards */}
            {resolvedHazards.length > 0 && (
              <div>
                <h3 className="text-xl font-semibold text-zinc-100 mb-4">Recently Resolved</h3>
                <div className="space-y-3">
                  {resolvedHazards.slice(0, 5).map((hazard) => (
                    <GlassPanel key={hazard.assessment_id} className="flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-zinc-300 uppercase">{hazard.hazard_type}</span>
                        <span className="text-zinc-500 text-sm ml-3">
                          Resolved {getTimeSince(hazard.created_at)}
                        </span>
                      </div>
                      <StatusBadge status="RESOLVED" variant="hazard" size="sm" />
                    </GlassPanel>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
