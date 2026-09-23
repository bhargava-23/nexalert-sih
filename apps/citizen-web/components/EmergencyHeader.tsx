'use client'

// Emergency First Viewport - Priority information per spec Section 3

import { GlassCard } from '@/components/ui/GlassCard'
import type { Incident, IncidentHazardAssessment, Location } from '@/types'
import {
  getHazardIcon,
  getHazardTypeName,
  formatDistance,
  formatTimestamp,
  getTimeSince,
  getDirection,
} from '@/lib/utils'

interface EmergencyHeaderProps {
  incident: Incident
  hazard: IncidentHazardAssessment
  distanceKm: number
  userLocation: Location | null
}

export function EmergencyHeader({
  incident,
  hazard,
  distanceKm,
  userLocation,
}: EmergencyHeaderProps) {
  const icon = getHazardIcon(hazard.hazard_type)
  const name = getHazardTypeName(hazard.hazard_type)
  const state = hazard.state || 'UNKNOWN'
  const isCritical = state === 'CRITICAL'

  // Calculate direction only when both locations exist
  const direction =
    userLocation && incident.centroid
      ? getDirection(
          userLocation.lat,
          userLocation.lon,
          incident.centroid.lat,
          incident.centroid.lon
        )
      : null

  return (
    <GlassCard className={`border-2 ${isCritical ? 'border-red-500' : 'border-yellow-500'} ${isCritical ? 'bg-red-500/10' : 'bg-yellow-500/10'}`}>
      <div className="flex items-start gap-4 mb-4">
        <div className="text-5xl">{icon}</div>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-zinc-100 mb-2">
            {name} Alert
          </h2>
          <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-semibold mb-3 ${
              isCritical
                ? 'bg-red-500/20 text-red-300 border border-red-500/50'
                : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50'
            }`}
          >
            {isCritical ? '🚨' : '⚠️'} {state}
          </div>
          <p className="text-base text-zinc-300 mb-2">
            {direction
              ? `${name} detected ~${formatDistance(distanceKm)} ${direction}`
              : `${name} detected in monitored area`}
          </p>
          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>
              LIVE • Updated {formatTimestamp(incident.last_observed_at)} •{' '}
              {getTimeSince(incident.last_observed_at)}
            </span>
          </div>
        </div>
      </div>

      <div className="border-t border-white/10 pt-4">
        <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wide">
          Recommended Action
        </p>
        <p className="text-base font-medium text-zinc-200">
          {isCritical
            ? 'Follow local authority instructions and evacuation guidance'
            : 'Monitor the situation and follow updates from local authorities'}
        </p>
      </div>
    </GlassCard>
  )
}
