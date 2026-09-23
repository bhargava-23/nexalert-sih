// Core Types for NexAlert Authority Dashboard

export interface Location {
  lat: number
  lon: number
  alt?: number
}

export interface TelemetryRecord {
  telemetry_id: string
  node_id: string
  sequence: number
  measurement_timestamp: string
  received_timestamp: string
  source: string
  location: Location | null
  measurements: {
    temp_c?: number | null
    humidity_pct?: number | null
    pressure_hpa?: number | null
    gas_adc?: number | null
    vibration_mps2?: number | null
    pm25_ug_m3?: number | null
    pm10_ug_m3?: number | null
    water_level_m?: number | null
    rainfall_mm_h?: number | null
    soil_moisture_vwc_pct?: number | null
  }
  diagnostics: Record<string, any>
  power?: {
    battery_pct?: number | null
    voltage_mv?: number | null
  } | null
  schema_version: string
}

export interface SensorAssessment {
  assessment_id: number
  telemetry_id: string
  node_id: string
  sensor_type: string
  health?: number | null
  quality?: number | null
  reliability?: number | null
  baseline_state?: string | null
  anomaly?: number | null
  created_at: string
}

export interface HazardAssessment {
  assessment_id: number
  telemetry_id: string
  hazard_type: string
  evidence?: number | null
  confidence?: number | null
  severity?: number | null
  risk?: number | null
  operational_risk?: number | null
  state?: string | null
  information_condition?: string | null
  created_at: string
}

export interface Node {
  node_id: string
  status: string
  location: Location | null
  last_telemetry_at?: string | null
  battery_pct?: number | null
  current_hazard_state?: string | null
  created_at: string
  updated_at: string
}

export type HazardState = 'NORMAL' | 'WATCH' | 'SUSPECTED' | 'CONFIRMED' | 'CRITICAL' | 'RESOLVED'
export type InformationCondition = 'GOOD' | 'DEGRADED' | 'UNKNOWN'
export type HazardType = 'fire' | 'flood' | 'seismic' | 'landslide'
