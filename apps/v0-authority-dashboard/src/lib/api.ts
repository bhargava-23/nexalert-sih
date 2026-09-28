/**
 * NexAlert Backend API Client
 *
 * Real backend integration - NO mock data.
 * Base URL: https://ideal-schema-stars-mounted.trycloudflare.com/api/v1
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://ideal-schema-stars-mounted.trycloudflare.com/api/v1';

// Backend response types (from actual FastAPI routes)
export interface BackendNode {
  node_id: string;
  status: string;
  location: {
    lat: number;
    lon: number;
  } | null;
  firmware_version: string | null;
  config_version: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendTelemetry {
  telemetry_id: string;
  node_id: string;
  sequence: number;
  measurement_timestamp: string;
  received_timestamp: string;
  source: string;
  location: {
    lat: number;
    lon: number;
  } | null;
  measurements: Record<string, number | null>;
  diagnostics: Record<string, any>;
  power: Record<string, number | string | null> | null;
  schema_version: string;
}

export interface BackendHazard {
  assessment_id: number;
  telemetry_id: string;
  hazard_type: string;
  evidence: number | null;
  confidence: number | null;
  severity: number | null;
  risk: number | null;
  state: string | null;
  information_condition: string | null;
  created_at: string;
}

export interface BackendIncident {
  incident_id: string;
  state: string;
  severity: string;
  location_geom: any;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface BackendSOSRequest {
  sos_id: string;
  status: string;
  location_lat?: number;
  location_lon?: number;
  message?: string;
  device_info?: string;
  created_at: string;
  updated_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

export interface BackendRegionalHazard {
  assessment_id: number;
  hazard_type: string;
  regional_state: string;
  regional_severity: string;
  regional_confidence: number;
  regional_risk: number;
  information_condition: string;
  node_count: number;
  updated_at: string;
}

/**
 * Backend-authoritative fire geometry
 * GeoJSON FeatureCollection with CURRENT/WARNING/PROJECTION zones
 * DO NOT calculate or generate geometry in frontend
 */
export interface IncidentGeometry {
  type: 'FeatureCollection';
  features: Array<{
    type: 'Feature';
    properties: {
      zone_type: 'CURRENT' | 'WARNING' | 'PROJECTION';
      area_hectares: number;
      perimeter_m: number | null;
    };
    geometry: any; // GeoJSON Polygon geometry
  }>;
}

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const text = await response.text();
      throw new APIError(
        response.status,
        `HTTP ${response.status}: ${response.statusText}`,
        text
      );
    }

    // Handle empty responses
    const text = await response.text();
    if (!text) {
      return [] as unknown as T;
    }

    return JSON.parse(text) as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(0, `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export const api = {
  /**
   * Get all nodes from backend
   * Returns actual field nodes like NODE-001
   */
  async getNodes(): Promise<BackendNode[]> {
    return fetchJSON<BackendNode[]>('/nodes');
  },

  /**
   * Get specific node by ID
   */
  async getNode(nodeId: string): Promise<BackendNode> {
    return fetchJSON<BackendNode>(`/nodes/${nodeId}`);
  },

  /**
   * Get latest telemetry from all nodes
   */
  async getLatestTelemetry(): Promise<BackendTelemetry[]> {
    return fetchJSON<BackendTelemetry[]>('/telemetry/latest');
  },

  /**
   * Get telemetry history for a specific node
   */
  async getNodeTelemetry(nodeId: string, limit: number = 100): Promise<BackendTelemetry[]> {
    return fetchJSON<BackendTelemetry[]>(`/telemetry/${nodeId}?limit=${limit}`);
  },

  /**
   * Get all hazard assessments
   */
  async getHazards(): Promise<BackendHazard[]> {
    return fetchJSON<BackendHazard[]>('/hazards');
  },

  /**
   * Get hazard assessments for a specific node
   */
  async getNodeHazards(nodeId: string): Promise<BackendHazard[]> {
    return fetchJSON<BackendHazard[]>(`/nodes/${nodeId}/hazard-assessments`);
  },

  /**
   * Get sensor assessments for a specific node
   */
  async getNodeSensorAssessments(nodeId: string): Promise<any[]> {
    return fetchJSON<any[]>(`/nodes/${nodeId}/sensor-assessments`);
  },

  /**
   * Get all incidents (Track B2)
   */
  async getIncidents(): Promise<BackendIncident[]> {
    return fetchJSON<BackendIncident[]>('/incidents');
  },

  /**
   * Get regional hazard assessments (Track B2)
   */
  async getRegionalHazards(): Promise<BackendRegionalHazard[]> {
    return fetchJSON<BackendRegionalHazard[]>('/regional-hazards');
  },

  /**
   * Get fire geometry for an incident (CURRENT/WARNING/PROJECTION zones)
   * Backend-authoritative geometry - DO NOT calculate or generate in frontend
   *
   * CRITICAL: Geometry comes from backend FireSimulation → FireGeometry
   * Frontend ONLY renders the returned GeoJSON, never calculates zones
   */
  async getIncidentGeometry(incidentId: string): Promise<IncidentGeometry> {
    // Note: Geometry endpoint is /api/incidents/{id}/geometries (not under /api/v1)
    return fetchJSON<IncidentGeometry>(`/../incidents/${incidentId}/geometries`);
  },

  /**
   * Get API health status
   */
  async getHealth(): Promise<{ status: string; timestamp: string; database: string }> {
    return fetchJSON('/health');
  },

  /**
   * Get all SOS emergency requests
   */
  async getSOSRequests(status?: string): Promise<BackendSOSRequest[]> {
    const params = status ? `?status=${status}` : '';
    return fetchJSON<BackendSOSRequest[]>(`/sos${params}`);
  },

  /**
   * Update SOS request status
   */
  async updateSOSStatus(sosId: string, status: string): Promise<BackendSOSRequest> {
    return fetchJSON<BackendSOSRequest>(`/sos/${sosId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },
};

export { APIError };
