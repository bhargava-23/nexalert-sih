'use client'

import { useState, useEffect } from 'react'

export default function CitizenEmergencyPage() {
  const [alert, setAlert] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for active critical incidents
    fetch('http://localhost:8000/api/incidents?state=CRITICAL')
      .then(res => res.json())
      .then(data => {
        if (data.incidents && data.incidents.length > 0) {
          setAlert(data.incidents[0])
        }
        setLoading(false)
      })
      .catch(() => {
        // Demo mode - show example alert (Phase 2C-3C: canonical model)
        setAlert({
          state: 'CRITICAL',
          centroid_lat: 12.9716,
          centroid_lon: 77.5946,
          distance_km: 1.8,
          direction: 'NE',
          hazard_assessments: [{
            hazard_type: 'WILDFIRE',
            severity: 0.91,
            confidence: 0.89,
            state: 'CONFIRMED'
          }]
        })
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-950 flex items-center justify-center">
        <div className="text-stone-400">Loading...</div>
      </div>
    )
  }

  if (!alert) {
    return <SafeMode />
  }

  return <EmergencyAlert alert={alert} />
}

function EmergencyAlert({ alert }: { alert: any }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-red-950 to-stone-950 text-stone-50 p-4">
      <div className="max-w-md mx-auto pt-8">
        {/* Emergency Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center text-3xl animate-pulse">
              🚨
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-2">EMERGENCY ALERT</h1>
          <div className="text-red-400 text-sm uppercase tracking-wider">
            Immediate Action Required
          </div>
        </div>

        {/* Hazard Information */}
        <div className="bg-stone-900/80 backdrop-blur border-2 border-red-500/50 rounded-2xl p-6 mb-6">
          <div className="text-center mb-6">
            <div className="text-5xl font-bold text-red-400 mb-2">
              {alert.hazard_assessments?.[0]?.hazard_type || 'EMERGENCY'}
            </div>
            <div className="text-2xl font-bold">DETECTED</div>
          </div>

          <div className="space-y-4">
            <InfoRow label="Severity" value="CRITICAL" valueClass="text-red-400" />
            <InfoRow
              label="Distance"
              value={`${alert.distance_km || 1.8} km`}
              valueClass="text-yellow-400"
            />
            <InfoRow
              label="Direction"
              value={alert.direction || 'NE'}
              valueClass="text-yellow-400"
            />
            <InfoRow
              label="Updated"
              value="Just now"
              valueClass="text-stone-300"
            />
          </div>
        </div>

        {/* Action Required */}
        <div className="bg-red-500 text-white rounded-2xl p-6 mb-6 text-center">
          <div className="text-2xl font-bold mb-2">EVACUATE IMMEDIATELY</div>
          <div className="text-sm opacity-90">
            Move to designated safe location
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3 mb-8">
          <button className="w-full bg-stone-800 hover:bg-stone-700 border border-stone-600 text-white rounded-xl py-4 px-6 font-semibold text-lg transition-colors">
            📍 VIEW SAFE LOCATION
          </button>
          <button className="w-full bg-red-600 hover:bg-red-700 text-white rounded-xl py-4 px-6 font-semibold text-lg transition-colors">
            🆘 EMERGENCY SOS
          </button>
        </div>

        {/* Emergency Info */}
        <div className="bg-stone-900/50 rounded-xl p-4 text-sm text-stone-400 text-center">
          <div className="mb-2">
            <strong className="text-stone-300">Emergency Services:</strong> 112
          </div>
          <div>
            Follow official evacuation routes and instructions
          </div>
        </div>
      </div>
    </div>
  )
}

function SafeMode() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-950 to-stone-950 text-stone-50 p-4">
      <div className="max-w-md mx-auto pt-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center text-3xl">
              ✓
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-2">ALL CLEAR</h1>
          <div className="text-emerald-400 text-sm uppercase tracking-wider">
            No Active Emergencies
          </div>
        </div>

        <div className="bg-stone-900/80 backdrop-blur border border-stone-700 rounded-2xl p-6 mb-6">
          <div className="text-center text-stone-300">
            <p className="mb-4">Your area is currently safe.</p>
            <p className="text-sm text-stone-400">
              NexAlert is monitoring environmental conditions 24/7.
              You will be notified immediately if any hazard is detected.
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <button className="w-full bg-stone-800 hover:bg-stone-700 border border-stone-600 text-white rounded-xl py-4 px-6 font-semibold transition-colors">
            📊 VIEW STATUS
          </button>
          <button className="w-full bg-stone-800 hover:bg-stone-700 border border-stone-600 text-white rounded-xl py-4 px-6 font-semibold transition-colors">
            🆘 EMERGENCY SOS
          </button>
        </div>
      </div>
    </div>
  )
}

function InfoRow({ label, value, valueClass }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-stone-700">
      <span className="text-stone-400 text-sm">{label}</span>
      <span className={`font-mono font-bold ${valueClass || ''}`}>{value}</span>
    </div>
  )
}
