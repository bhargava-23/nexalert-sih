// NexAlert Citizen API Client
// Centralized API access - verified against backend routes

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

import type { Incident, TelemetryRecord, Node } from '@/types'

// Real backend endpoints only
export const api = {
  /**
   * Get active incidents from Track B2
   * GET /api/incidents?active_only=true&limit=20
   */
  async getActiveIncidents(): Promise<Incident[]> {
    const response = await fetch(`${API_BASE}/incidents?active_only=true&limit=20`)
    if (!response.ok) {
      throw new Error(`Failed to fetch incidents: ${response.statusText}`)
    }
    return response.json()
  },

  /**
   * Get latest telemetry from Track B1
   * GET /api/telemetry/latest
   */
  async getLatestTelemetry(): Promise<TelemetryRecord[]> {
    const response = await fetch(`${API_BASE}/telemetry/latest`)
    if (!response.ok) {
      throw new Error(`Failed to fetch telemetry: ${response.statusText}`)
    }
    return response.json()
  },

  /**
   * Get nodes
   * GET /api/nodes
   */
  async getNodes(): Promise<Node[]> {
    const response = await fetch(`${API_BASE}/nodes`)
    if (!response.ok) {
      throw new Error(`Failed to fetch nodes: ${response.statusText}`)
    }
    return response.json()
  },

  /**
   * Health check
   * GET /api/health
   */
  async getHealth(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${API_BASE}/health`)
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`)
    }
    return response.json()
  },
}
