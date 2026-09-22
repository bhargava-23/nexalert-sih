'use client'

// SystemStatus - Overall system health metrics

import { MetricCard } from '@/components/ui/MetricCard'
import { SectionHeader } from '@/components/ui/SectionHeader'

interface SystemStatusProps {
  activeNodes: number
  totalNodes: number
  activeHazards: number
  lastUpdate: string
}

export function SystemStatus({
  activeNodes,
  totalNodes,
  activeHazards,
  lastUpdate
}: SystemStatusProps) {
  const nodeHealth = totalNodes > 0 ? (activeNodes / totalNodes) : 0

  return (
    <div>
      <SectionHeader
        title="System Status"
        subtitle={`Last updated: ${lastUpdate}`}
      />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Active Nodes"
          value={activeNodes}
          unit={`/ ${totalNodes}`}
          status={nodeHealth >= 0.8 ? 'good' : nodeHealth >= 0.5 ? 'warning' : 'critical'}
        />
        <MetricCard
          label="Active Hazards"
          value={activeHazards}
          status={activeHazards === 0 ? 'good' : activeHazards <= 2 ? 'warning' : 'critical'}
        />
        <MetricCard
          label="System Health"
          value={`${(nodeHealth * 100).toFixed(0)}%`}
          status={nodeHealth >= 0.8 ? 'good' : nodeHealth >= 0.5 ? 'warning' : 'critical'}
        />
      </div>
    </div>
  )
}
