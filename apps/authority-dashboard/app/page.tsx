'use client'

// Dashboard Overview - Main landing page

import { useEffect, useState } from 'react'
import { SystemStatus } from '@/components/dashboard/SystemStatus'
import { NodeGrid } from '@/components/dashboard/NodeGrid'
import { HazardSummary } from '@/components/dashboard/HazardSummary'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { api } from '@/lib/api'
import { formatTimestamp, getTimeSince } from '@/lib/utils'
import type { Node, HazardAssessment } from '@/types'

export default function DashboardPage() {
  const [nodes, setNodes] = useState<Node[]>([])
  const [hazards, setHazards] = useState<HazardAssessment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  const fetchDashboardData = async () => {
    try {
      setError(null)
      const [nodesData, hazardsData] = await Promise.all([
        api.getNodes(),
        api.getGlobalHazards()
      ])

      setNodes(nodesData)
      setHazards(hazardsData)
      setLastUpdate(formatTimestamp(new Date().toISOString()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()

    // Poll for updates every 10 seconds
    const interval = setInterval(fetchDashboardData, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-zinc-400">Loading NexAlert Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <ErrorState
            title="Dashboard Error"
            message={error}
            onRetry={fetchDashboardData}
          />
        </div>
      </div>
    )
  }

  const activeNodes = nodes.filter(n => n.status === 'ACTIVE').length
  const activeHazards = hazards.filter(h =>
    h.state && !['NORMAL', 'RESOLVED'].includes(h.state)
  ).length

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-zinc-100 mb-2">
            NexAlert Command Center
          </h1>
          <p className="text-zinc-400">
            Real-time hazard monitoring and intelligence
          </p>
        </div>

        {/* System Status */}
        <div className="mb-8">
          <SystemStatus
            activeNodes={activeNodes}
            totalNodes={nodes.length}
            activeHazards={activeHazards}
            lastUpdate={lastUpdate}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Nodes (2/3 width) */}
          <div className="lg:col-span-2">
            <NodeGrid nodes={nodes} />
          </div>

          {/* Right Column - Hazards (1/3 width) */}
          <div className="lg:col-span-1">
            <HazardSummary hazards={hazards} />
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center text-xs text-zinc-600">
          <p>Backend: {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}</p>
          <p className="mt-1">Auto-refresh: 10s</p>
        </div>
      </div>
    </div>
  )
}
