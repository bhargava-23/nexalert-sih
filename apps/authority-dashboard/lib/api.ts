// API Client for NexAlert Backend

import type { TelemetryRecord, SensorAssessment, HazardAssessment, Node } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

async function fetchJSON<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`)

  if (!response.ok) {
    throw new APIError(
      response.status,
      `API request failed: ${response.statusText}`
    )
  }

  return response.json()
}

export const api = {
  // Telemetry endpoints
  async getLatestTelemetry(): Promise<TelemetryRecord[]> {
    return fetchJSON<TelemetryRecord[]>('/telemetry/latest')
  },

  async getNodeTelemetry(nodeId: string, limit: number = 100): Promise<TelemetryRecord[]> {
    return fetchJSON<TelemetryRecord[]>(`/telemetry/${nodeId}?limit=${limit}`)
  },

  // Node endpoints
  async getNodes(): Promise<Node[]> {
    return fetchJSON<Node[]>('/nodes')
  },

  async getNode(nodeId: string): Promise<Node> {
    return fetchJSON<Node>(`/nodes/${nodeId}`)
  },

  // Sensor assessment endpoints
  async getGlobalSensorAssessments(): Promise<SensorAssessment[]> {
    return fetchJSON<SensorAssessment[]>('/sensor-assessments')
  },

  async getNodeSensorAssessments(nodeId: string): Promise<SensorAssessment[]> {
    return fetchJSON<SensorAssessment[]>(`/nodes/${nodeId}/sensor-assessments`)
  },

  // Hazard assessment endpoints
  async getGlobalHazards(): Promise<HazardAssessment[]> {
    return fetchJSON<HazardAssessment[]>('/hazards')
  },

  async getNodeHazardAssessments(nodeId: string): Promise<HazardAssessment[]> {
    return fetchJSON<HazardAssessment[]>(`/nodes/${nodeId}/hazard-assessments`)
  },

  // Health check
  async getHealth(): Promise<{ status: string; timestamp: string; database: string }> {
    return fetchJSON('/health')
  },
}

export { APIError }
