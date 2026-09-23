// NexAlert Citizen UI Type Definitions
// Real backend data types only - NO fake emergency data

export interface Location {
  lat: number
  lon: number
}

export interface Centroid {
  lat: number
  lon: number
}

// Track B1: Base telemetry
export interface TelemetryRecord {
  telemetry_id: string
  node_id: string
  sequence: number
  measurement_timestamp: string // ISO 8601 UTC
  received_timestamp: string // ISO 8601 UTC
  source: string
  location: Location | null
  measurements: {
    temp_c?: number
    humidity_pct?: number
    pressure_hpa?: number
    [key: string]: number | undefined
  }
  diagnostics: Record<string, any>
  power: {
    voltage_mv?: number
    percentage?: number
  } | null
  schema_version: string
}

// Track B2: Incident hazard assessment (Phase 2C canonical model)
export interface IncidentHazardAssessment {
  assessment_id: number
  hazard_type: string
  evidence: number | null
  confidence: number | null
  severity: number | null
  operational_risk: number | null
  state: string | null
  information_condition: string | null
  hazard_specific_data: Record<string, any> | null
  assessment_timestamp: string
  model_version: string | null
  source_summary: Record<string, any> | null
  created_at: string
}

// Track B2: Incident (correlation container)
export interface Incident {
  incident_id: string
  state: string
  information_condition: string | null
  hazard_assessments: IncidentHazardAssessment[]
  centroid: Centroid | null
  first_observed_at: string
  last_observed_at: string
  resolved_at: string | null
  source_summary: Record<string, any> | null
  created_by: string
  current_version: number
  created_at: string
  updated_at: string
}

// Node info
export interface Node {
  node_id: string
  status: string
  location: Location | null
  firmware_version: string | null
  config_version: string | null
  created_at: string
  updated_at: string
}

// Citizen geolocation state
export interface GeolocationState {
  latitude: number | null
  longitude: number | null
  accuracy: number | null
  error: string | null
  loading: boolean
}

// Computed nearest hazard (client-side only)
export interface NearestHazard {
  incident: Incident
  hazard: IncidentHazardAssessment
  distanceKm: number
}
