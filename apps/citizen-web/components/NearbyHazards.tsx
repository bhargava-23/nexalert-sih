'use client'

// Nearby hazards list - real backend data only

import { GlassCard } from '@/components/ui/GlassCard'
import type { Incident, Location } from '@/types'
import {
  getHazardIcon,
  getHazardTypeName,
  calculateDistance,
  formatDistance,
  getTimeSince,
} from '@/lib/utils'

interface NearbyHazardsProps {
  incidents: Incident[]
  currentIncidentId?: string
  userLocation: Location | null
}

export function NearbyHazards({
  incidents,
  currentIncidentId,
  userLocation,
}: NearbyHazardsProps) {
  // Filter out current emergency if specified
  const otherIncidents = currentIncidentId
    ? incidents.filter((inc) => inc.incident_id !== currentIncidentId)
    : incidents

  if (otherIncidents.length === 0) {
    return null
  }

  // Calculate distances and sort
  const incidentsWithDistance = otherIncidents
    .map((incident) => {
      let distance: number | null = null
      if (userLocation && incident.centroid) {
        distance = calculateDistance(
          userLocation.lat,
          userLocation.lon,
          incident.centroid.lat,
          incident.centroid.lon
        )
      }
      return { incident, distance }
    })
    .sort((a, b) => {
      if (a.distance === null) return 1
      if (b.distance === null) return -1
      return a.distance - b.distance
    })

  return (
    <GlassCard>
      <h3 className="font-semibold text-zinc-100 mb-3 flex items-center gap-2">
        <span>🚨</span>
        <span>
          {currentIncidentId ? 'Other Active Hazards' : 'Active Hazards'}
        </span>
      </h3>
      <div className="space-y-3">
        {incidentsWithDistance.slice(0, 5).map(({ incident, distance }) => {
          const primaryHazard = incident.hazard_assessments[0]
          if (!primaryHazard) return null

          const icon = getHazardIcon(primaryHazard.hazard_type)
          const name = getHazardTypeName(primaryHazard.hazard_type)
          const state = primaryHazard.state || 'UNKNOWN'

          return (
            <div
              key={incident.incident_id}
              className="flex items-start gap-3 p-3 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition-colors"
            >
              <div className="text-2xl">{icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-zinc-100 text-sm">{name}</p>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      state === 'CONFIRMED' || state === 'CRITICAL'
                        ? 'bg-red-500/20 text-red-300'
                        : 'bg-yellow-500/20 text-yellow-300'
                    }`}
                  >
                    {state}
                  </span>
                </div>
                {distance !== null && (
                  <p className="text-xs text-zinc-400 mb-1">
                    ~{formatDistance(distance)} away
                  </p>
                )}
                <p className="text-xs text-zinc-500">
                  Detected {getTimeSince(incident.first_observed_at)}
                </p>
              </div>
            </div>
          )
        })}
      </div>
      {incidentsWithDistance.length > 5 && (
        <p className="text-xs text-zinc-500 mt-3 text-center">
          {incidentsWithDistance.length - 5} more {incidentsWithDistance.length - 5 === 1 ? 'hazard' : 'hazards'} monitored
        </p>
      )}
    </GlassCard>
  )
}
