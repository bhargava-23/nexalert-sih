'use client'

// NexAlert Citizen Safety Experience
// ONE PAGE: Normal Mode ↔ Emergency Mode transformation
// Spec: docs/specification_text/14_citizen_safety_ui.md

import { useEffect, useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { LoadingState } from '@/components/ui/LoadingSpinner'
import { ErrorState } from '@/components/ui/ErrorState'
import { EmergencyHeader } from '@/components/EmergencyHeader'
import { SafetyStatus } from '@/components/SafetyStatus'
import { LocationHeader } from '@/components/LocationHeader'
import { NearbyHazards } from '@/components/NearbyHazards'
import { EnvironmentalConditions } from '@/components/EnvironmentalConditions'
import { EmergencyActions } from '@/components/EmergencyActions'
import { api } from '@/lib/api'
import type { Incident, TelemetryRecord, GeolocationState, NearestHazard } from '@/types'
import { calculateDistance } from '@/lib/utils'

export default function CitizenPage() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [telemetry, setTelemetry] = useState<TelemetryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [location, setLocation] = useState<GeolocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    error: null,
    loading: false,
  })

  const fetchData = async () => {
    try {
      setError(null)
      const [incidentsData, telemetryData] = await Promise.all([
        api.getActiveIncidents(),
        api.getLatestTelemetry(),
      ])
      setIncidents(incidentsData)
      setTelemetry(telemetryData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load safety data')
      console.error('Data fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000) // Poll every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocation((prev) => ({ ...prev, error: 'Geolocation not supported' }))
      return
    }

    setLocation((prev) => ({ ...prev, loading: true, error: null }))

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          error: null,
          loading: false,
        })
      },
      (error) => {
        setLocation((prev) => ({
          ...prev,
          error: error.message || 'Location unavailable',
          loading: false,
        }))
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    )
  }

  // Find nearest hazard with CONFIRMED or CRITICAL state
  const getNearestEmergency = (): NearestHazard | null => {
    if (!location.latitude || !location.longitude || incidents.length === 0) {
      return null
    }

    let nearest: NearestHazard | null = null
    let minDistance = Infinity

    incidents.forEach((incident) => {
      // Only consider incidents with confirmed/critical hazards
      const emergencyHazards = incident.hazard_assessments.filter(
        (h) => h.state === 'CONFIRMED' || h.state === 'CRITICAL'
      )

      if (emergencyHazards.length > 0 && incident.centroid) {
        const distance = calculateDistance(
          location.latitude!,
          location.longitude!,
          incident.centroid.lat,
          incident.centroid.lon
        )

        if (distance < minDistance) {
          minDistance = distance
          nearest = {
            incident,
            hazard: emergencyHazards[0], // Primary hazard
            distanceKm: distance,
          }
        }
      }
    })

    return nearest
  }

  const nearestEmergency = getNearestEmergency()

  // EMERGENCY MODE: Any CONFIRMED or CRITICAL hazard exists
  const isEmergencyMode = nearestEmergency !== null

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingState message="Loading safety information..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <ErrorState
          title="Connection Error"
          message={error}
          onRetry={fetchData}
        />
      </div>
    )
  }

  // SAME PAGE - transforms based on mode
  return (
    <div className="min-h-screen pb-8">
      <LocationHeader
        location={location}
        onRequestLocation={requestLocation}
        emergencyMode={isEmergencyMode}
      />

      <div className="max-w-screen-sm mx-auto px-4 py-6 space-y-6">
        {isEmergencyMode && nearestEmergency ? (
          <>
            {/* EMERGENCY MODE */}
            <EmergencyHeader
              incident={nearestEmergency.incident}
              hazard={nearestEmergency.hazard}
              distanceKm={nearestEmergency.distanceKm}
              userLocation={
                location.latitude && location.longitude
                  ? { lat: location.latitude, lon: location.longitude }
                  : null
              }
            />

            <EmergencyActions />

            <NearbyHazards
              incidents={incidents}
              currentIncidentId={nearestEmergency.incident.incident_id}
              userLocation={
                location.latitude && location.longitude
                  ? { lat: location.latitude, lon: location.longitude }
                  : null
              }
            />

            <EnvironmentalConditions telemetry={telemetry} />

            <GlassCard className="bg-red-500/5 border-red-500/20">
              <div className="flex items-start gap-3">
                <div className="text-2xl">ℹ️</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-300 mb-1">
                    Emergency Alert Active
                  </p>
                  <p className="text-xs text-zinc-400">
                    Follow local authority instructions and official emergency guidance. NexAlert monitoring system is operational.
                  </p>
                </div>
              </div>
            </GlassCard>
          </>
        ) : (
          <>
            {/* NORMAL MODE */}
            <SafetyStatus
              incidents={incidents}
              telemetry={telemetry}
            />

            <EmergencyActions normalMode={true} />

            {incidents.length > 0 && (
              <NearbyHazards
                incidents={incidents}
                userLocation={
                  location.latitude && location.longitude
                    ? { lat: location.latitude, lon: location.longitude }
                    : null
                }
              />
            )}

            <EnvironmentalConditions telemetry={telemetry} />

            <GlassCard className="bg-blue-500/5 border-blue-500/20">
              <div className="flex items-center gap-3">
                <div className="text-2xl">ℹ️</div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-300 mb-1">
                    NexAlert Monitoring Active
                  </p>
                  <p className="text-xs text-zinc-400">
                    Real-time environmental monitoring and hazard detection system operational. You&apos;ll be notified immediately if any hazard is detected.
                  </p>
                </div>
              </div>
            </GlassCard>
          </>
        )}
      </div>
    </div>
  )
}
