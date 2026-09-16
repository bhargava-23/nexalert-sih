'use client'

import { useState, useEffect } from 'react'

// Canonical telemetry structure matching backend API
interface CanonicalTelemetry {
  telemetry_id: string
  node_id: string
  sequence: number
  measurement_timestamp: string  // ISO 8601
  received_timestamp: string     // ISO 8601
  source: string
  location: {
    lat: number
    lon: number
    alt?: number
  } | null
  measurements: {
    temp_c?: number | null
    humidity_pct?: number | null
    pressure_hpa?: number | null
    pm25_ug_m3?: number | null
    pm10_ug_m3?: number | null
  }
  diagnostics: {
    uptime_s?: number
    self_test_passed?: boolean
    comm_integrity?: number
    calibration_valid?: boolean
    stability_index?: number
  }
  power: {
    battery_pct?: number | null
    battery_voltage?: number | null
    solar_current?: number | null
  } | null
  schema_version: string
}

export default function DashboardPage() {
  const [systemStatus, setSystemStatus] = useState<'operational' | 'degraded' | 'offline'>('operational')
  const [mqttStatus, setMqttStatus] = useState<'connected' | 'disconnected'>('connected')
  const [telemetry, setTelemetry] = useState<CanonicalTelemetry | null>(null)
  const [incidents, setIncidents] = useState<any[]>([])
  const [demoMode, setDemoMode] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check backend health
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(() => setSystemStatus('operational'))
      .catch(() => setSystemStatus('degraded'))

    // Fetch operational telemetry from canonical endpoint
    fetch('http://localhost:8000/api/telemetry/NODE-001?limit=1')
      .then(res => {
        if (!res.ok) throw new Error('Telemetry not found')
        return res.json()
      })
      .then(data => {
        // Extract latest telemetry from array response
        const latestTelemetry: CanonicalTelemetry = data[0]
        if (!latestTelemetry) throw new Error('No telemetry available')

        setTelemetry(latestTelemetry)
        setDemoMode(false)
        setLoading(false)
      })
      .catch(() => {
        // Fallback to demo data (isolated demo mode)
        const demoData = {
          node_id: 'NEX-001',
          status: 'ONLINE',
          telemetry: {
            temperature: 31.4,
            humidity: 58.2,
            pressure: 1009.8,
            gas_smoke: 'normal',
            vibration: 'normal',
            last_update: new Date().toISOString()
          }
        }
        // Demo mode uses non-canonical shape (intentional isolation)
        setTelemetry(null)
        setDemoMode(true)
        setLoading(false)
      })

    // Fetch incidents
    fetch('http://localhost:8000/incidents')
      .then(res => res.json())
      .then(data => setIncidents(data.incidents || []))
      .catch(() => {})
  }, [])

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <header className="border-b border-zinc-800/50 bg-black/95 backdrop-blur">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-white rounded" />
              <span className="text-sm font-semibold tracking-wide">NEXORA</span>
            </div>
            <nav className="flex items-center gap-6 text-sm">
              <button className="text-zinc-400 hover:text-white transition-colors">Overview</button>
              <button className="px-3 py-1.5 bg-white text-black rounded-md font-medium">Investigations</button>
              <button className="text-zinc-400 hover:text-white transition-colors">Library</button>
              <button className="text-zinc-400 hover:text-white transition-colors">Operations</button>
              <button className="text-zinc-400 hover:text-white transition-colors">Settings</button>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-zinc-800/50 rounded-lg transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
            <button className="p-2 hover:bg-zinc-800/50 rounded-lg transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>
            <div className="flex items-center gap-3 pl-4 border-l border-zinc-800">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full" />
              <div className="text-sm">
                <div className="font-medium">Marina Wilson</div>
                <div className="text-xs text-zinc-500">Senior Investigator</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold mb-1">Investigations</h1>
          <p className="text-sm text-zinc-500">Review and track all active investigations</p>
        </div>

        {/* Top Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {/* Escalated Cases */}
          <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5">
            <div className="text-zinc-400 text-xs mb-3 uppercase tracking-wide">Escalated Cases</div>
            <div className="flex items-end justify-between">
              <div className="text-4xl font-bold">32</div>
              <div className="text-xs text-green-400 flex items-center gap-1">
                <span>↓ 12%</span>
                <span className="text-zinc-600">vs last 7 days</span>
              </div>
            </div>
            {/* Mini sparkline */}
            <div className="mt-4 h-12 flex items-end gap-0.5">
              {[40, 35, 45, 30, 50, 38, 32, 45, 28, 35, 40, 32].map((h, i) => (
                <div key={i} className="flex-1 bg-zinc-700/30 rounded-t" style={{ height: `${h}%` }} />
              ))}
            </div>
          </div>

          {/* Estimated Time Saved */}
          <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5">
            <div className="text-zinc-400 text-xs mb-3 uppercase tracking-wide">Estimated time saved</div>
            <div className="text-4xl font-bold mb-1">32H 34M</div>
            <div className="text-xs text-zinc-500 mt-2">+30% vs last 7 days</div>
            {/* Mini line chart */}
            <div className="mt-4 h-12">
              <svg viewBox="0 0 100 30" className="w-full h-full" preserveAspectRatio="none">
                <polyline
                  points="0,25 10,20 20,22 30,18 40,15 50,12 60,14 70,10 80,8 90,10 100,6"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  className="text-zinc-600"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>
            </div>
          </div>

          {/* Sources */}
          <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5">
            <div className="text-zinc-400 text-xs mb-3 uppercase tracking-wide">Sources</div>
            <div className="flex items-center justify-center h-24">
              <div className="relative w-28 h-28">
                <svg viewBox="0 0 100 100" className="transform -rotate-90">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-zinc-800" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-white" strokeDasharray="251.2" strokeDashoffset="62.8" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold">90</div>
                  <div className="text-xs text-zinc-500">Total alerts</div>
                </div>
              </div>
            </div>
            <div className="mt-3 space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-white" />
                  <span className="text-zinc-400">MQTT Telemetry</span>
                </div>
                <span className="font-mono">52 - 63%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-zinc-600" />
                  <span className="text-zinc-400">REST Gateway</span>
                </div>
                <span className="font-mono">38 - 37%</span>
              </div>
            </div>
          </div>

          {/* Agent Determinations */}
          <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5">
            <div className="text-zinc-400 text-xs mb-3 uppercase tracking-wide">Agent Determinations</div>
            <div className="flex items-center justify-center h-24">
              <div className="relative w-28 h-28">
                <svg viewBox="0 0 100 100" className="transform -rotate-90">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-zinc-800" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="8" className="text-emerald-400" strokeDasharray="251.2" strokeDashoffset="125.6" strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-bold">32</div>
                </div>
              </div>
            </div>
            <div className="mt-3 space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-zinc-400">Malicious</span>
                </div>
                <span className="font-mono">16</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-zinc-600" />
                  <span className="text-zinc-400">Suspicious</span>
                </div>
                <span className="font-mono">16</span>
              </div>
            </div>
          </div>
        </div>

        {/* Investigations Flow + Incidents */}
        <div className="grid grid-cols-2 gap-4">
          {/* Investigations Flow */}
          <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-semibold">Investigations Flow</h2>
                <p className="text-xs text-zinc-500 mt-0.5">Track case progression</p>
              </div>
              <button className="px-3 py-1.5 text-xs border border-zinc-700 rounded-lg hover:bg-zinc-800/50 transition-colors">
                + Add Cases
              </button>
            </div>

            {/* Flow visualization */}
            <div className="relative h-64 flex items-center justify-between px-8">
              {/* Stages */}
              <div className="flex-1 flex items-center justify-between relative">
                {['Ingestion', 'Categorization', 'Assessment', 'Legal Review', 'Disposition'].map((stage, i) => (
                  <div key={stage} className="relative z-10">
                    <div className="text-xs text-zinc-500 mb-2">{stage}</div>
                    <div className="w-16 h-16 rounded-lg border border-zinc-700 bg-zinc-900 flex items-center justify-center">
                      <div className="text-2xl font-bold text-zinc-400">{[55, 28, 28, 25, 61][i]}</div>
                    </div>
                  </div>
                ))}
                {/* Connecting lines would go here */}
              </div>
            </div>
          </div>

          {/* Active Incidents */}
          <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-xl p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-semibold">Active Incidents</h2>
                <p className="text-xs text-zinc-500 mt-0.5">Real-time hazard monitoring</p>
              </div>
              <div className="text-xs text-zinc-500">{incidents.length} active</div>
            </div>

            <div className="space-y-3 max-h-64 overflow-y-auto">
              {incidents.length === 0 ? (
                <div className="text-center py-8 text-zinc-600 text-sm">
                  No active incidents
                </div>
              ) : (
                incidents.map((incident) => (
                  <IncidentCard key={incident.incident_id} incident={incident} />
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

function IncidentCard({ incident }: { incident: any }) {
  // Phase 2C-3C: Incident uses canonical hazard_assessments array only
  const hasHazardAssessments = incident.hazard_assessments && incident.hazard_assessments.length > 0

  if (!hasHazardAssessments) {
    // No assessment data available
    return (
      <div className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg p-3">
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className="text-sm font-medium text-zinc-200">Incident</div>
            <div className="text-xs text-zinc-500 mt-0.5">{incident.incident_id?.slice(0, 8)}</div>
          </div>
          <div className="px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-xs">
            {incident.state}
          </div>
        </div>
        <div className="text-xs text-zinc-500">No assessment data</div>
      </div>
    )
  }

  // Canonical path: Display per-hazard assessments
  return (
    <div className="bg-zinc-800/30 border border-zinc-700/50 rounded-lg p-3 hover:border-zinc-600/50 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-sm font-medium text-zinc-200">
            {incident.hazard_assessments.map((h: any) => h.hazard_type).join(' / ')}
          </div>
          <div className="text-xs text-zinc-500 mt-0.5">{incident.incident_id?.slice(0, 8)}</div>
        </div>
        <div className="px-2 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-xs">
          {incident.state}
        </div>
      </div>

      {/* Per-hazard assessments */}
      <div className="space-y-2">
        {incident.hazard_assessments.map((assessment: any, index: number) => (
          <div key={assessment.assessment_id || index}>
            <div className="text-xs font-medium text-zinc-400 mb-1.5">
              {assessment.hazard_type} Hazard
              {assessment.state && (
                <span className="ml-2 text-zinc-600">({assessment.state})</span>
              )}
            </div>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div>
                <div className="text-zinc-500 mb-1">Confidence</div>
                <div className="font-mono font-semibold text-zinc-200">
                  {assessment.confidence != null ? (assessment.confidence * 100).toFixed(0) + '%' : '—'}
                </div>
              </div>
              <div>
                <div className="text-zinc-500 mb-1">Severity</div>
                <div className="font-mono font-semibold text-zinc-200">
                  {assessment.severity != null ? (assessment.severity * 100).toFixed(0) + '%' : '—'}
                </div>
              </div>
              <div>
                <div className="text-zinc-500 mb-1">Risk</div>
                <div className="font-mono font-semibold text-zinc-200">
                  {assessment.operational_risk != null ? (assessment.operational_risk * 100).toFixed(0) + '%' : '—'}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
