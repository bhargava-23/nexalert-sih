/**
 * Frontend types for V0 Authority Dashboard
 * Maps backend data to UI-friendly formats
 */

import type { BackendNode, BackendTelemetry, BackendHazard, BackendIncident, BackendRegionalHazard } from '@/lib/api';
import { formatIST, formatISTTime, formatRelativeTime } from '@/lib/time';

// UI State types (keep from mock.ts)
export type State = 'NORMAL' | 'WATCH' | 'SUSPECTED' | 'CONFIRMED' | 'CRITICAL' | 'RESOLVED';
export type InformationCondition = 'GOOD' | 'DEGRADED' | 'UNKNOWN';
export type NodeState = 'ONLINE' | 'DEGRADED' | 'UNREACHABLE' | 'OFFLINE';

// Frontend Node interface (transformed from backend)
export interface Node {
  id: string;
  name: string;
  kind: 'Weather' | 'Camera' | 'Relay' | 'Seismic' | 'River gauge' | 'Unknown';
  location: string;
  coordinates: [number, number]; // [lat, lon] for Leaflet
  state: NodeState;
  lastSeen: string;
  battery: number;
  signal: string;
}

// Frontend Incident interface
export interface Incident {
  id: string;
  title: string;
  hazard: 'Wildfire' | 'Flooding' | 'Seismic' | 'Extreme heat' | 'Infrastructure' | 'Unknown';
  state: State;
  severity: 'Advisory' | 'Elevated' | 'Major' | 'Extreme';
  informationCondition: InformationCondition;
  freshness: string;
  location: string;
  updatedAt: string;
  footprint: string;
  evidence: string[];
  recommendation: string;
  humanAction: string;
}

// Frontend Telemetry interface
export interface TelemetryRecord {
  id: string;
  source: string;
  signal: string;
  observed: string;
  state: string;
  receivedAt: string;
  quality: InformationCondition;
  measurements?: Record<string, number | null>;
}

// SOS Request interface (placeholder - backend may not have this yet)
export interface SOSRequest {
  id: string;
  caller: string;
  location: string;
  receivedAt: string;
  state: 'NEW' | 'TRIAGED' | 'ASSIGNED' | 'RESOLVED';
  note: string;
  channel: 'Mobile' | 'Voice' | 'SMS';
}

// Alert Lifecycle interface (placeholder)
export interface AlertLifecycle {
  id: string;
  title: string;
  audience: string;
  state: 'DRAFT' | 'REVIEW' | 'AUTHORIZED' | 'ISSUED' | 'EXPIRED';
  channel: string;
  issuedAt?: string;
  owner: string;
  lastChange: string;
}

// Response Action interface (placeholder)
export interface ResponseAction {
  id: string;
  title: string;
  owner: string;
  state: 'PROPOSED' | 'AUTHORIZED' | 'IN PROGRESS' | 'COMPLETE' | 'BLOCKED';
  due: string;
  note: string;
}

// System Service interface (placeholder)
export interface SystemService {
  id: string;
  name: string;
  state: 'OPERATIONAL' | 'DEGRADED' | 'UNAVAILABLE';
  detail: string;
  lastCheck: string;
  dependency: string;
}

// Map Layer interface
export interface MapLayer {
  id: string;
  name: string;
  description: string;
  visible: boolean;
  icon: 'map' | 'nodes' | 'risk' | 'sos' | 'terrain';
}

// Hazard Geometry interface
export interface HazardGeometry {
  id: string;
  name: string;
  type: 'Current' | 'Warning' | 'Projection' | 'Operational buffer' | 'Impact';
  description: string;
  visible: boolean;
  color: string;
}

// Scenario interface
export interface Scenario {
  id: string;
  name: string;
  description: string;
  updated: string;
  mode: 'LIVE' | 'SIMULATION';
}

// Audit Event interface
export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  scope: string;
  result: 'Recorded' | 'Rejected' | 'Deferred';
}

/**
 * Transform backend node to frontend format
 */
export function transformNode(backend: BackendNode): Node {
  // Extract lat/lon from backend location object (NOT GeoJSON)
  const coordinates: [number, number] = backend.location
    ? [backend.location.lat, backend.location.lon]
    : [13.13495, 77.56681]; // NODE-001 known deployment location fallback

  // Determine node state from backend status
  const state: NodeState = backend.status === 'ACTIVE' ? 'ONLINE' : 'OFFLINE';

  // Calculate last seen from updated_at using relative time
  const lastSeen = formatRelativeTime(backend.updated_at);

  return {
    id: backend.node_id,
    name: backend.node_id, // Use node_id as name
    kind: 'Unknown', // Backend doesn't provide node type yet
    location: backend.node_id,
    coordinates,
    state,
    lastSeen,
    battery: 0, // Backend doesn't provide battery yet
    signal: '—', // Backend doesn't provide signal yet
  };
}

/**
 * Transform backend telemetry to frontend format
 */
export function transformTelemetry(backend: BackendTelemetry): TelemetryRecord {
  const measurements = backend.measurements || {};
  const diagnostics = backend.diagnostics || {};

  // Determine information condition from diagnostics
  const quality: InformationCondition = 'GOOD'; // Default, refine based on diagnostics

  // Format observed timestamp to IST time
  const observed = formatISTTime(backend.measurement_timestamp);

  // Format received timestamp to IST
  const receivedAt = formatIST(backend.received_timestamp);

  return {
    id: backend.telemetry_id,
    source: backend.node_id,
    signal: backend.source,
    observed,
    state: 'NORMAL', // Derive from hazard assessments
    receivedAt,
    quality,
    measurements: backend.measurements,
  };
}

/**
 * Transform backend hazard to determine state
 */
export function hazardToState(hazard: BackendHazard): State {
  const state = hazard.state?.toUpperCase();
  if (state === 'NORMAL' || state === 'WATCH' || state === 'SUSPECTED' ||
      state === 'CONFIRMED' || state === 'CRITICAL' || state === 'RESOLVED') {
    return state as State;
  }
  return 'NORMAL';
}

/**
 * Transform backend regional hazard to frontend incident
 */
export function transformRegionalHazard(backend: BackendRegionalHazard): Incident {
  const hazardMap: Record<string, Incident['hazard']> = {
    'fire': 'Wildfire',
    'flood': 'Flooding',
    'landslide': 'Seismic',
    'pollution': 'Infrastructure',
  };

  const severityMap: Record<string, Incident['severity']> = {
    'ADVISORY': 'Advisory',
    'ELEVATED': 'Elevated',
    'MAJOR': 'Major',
    'EXTREME': 'Extreme',
  };

  const state = backend.regional_state?.toUpperCase() as State || 'NORMAL';
  const severity = severityMap[backend.regional_severity] || 'Advisory';
  const hazard = hazardMap[backend.hazard_type] || 'Unknown';

  // Calculate freshness using relative time
  const freshness = formatRelativeTime(backend.updated_at);

  const informationCondition = backend.information_condition as InformationCondition || 'UNKNOWN';

  // Format updated timestamp to IST
  const updatedAt = formatIST(backend.updated_at);

  return {
    id: backend.regional_id?.toString() || 'unknown',
    title: `${hazard} incident`,
    hazard,
    state,
    severity,
    informationCondition,
    freshness,
    location: 'Regional',
    updatedAt,
    footprint: '—',
    evidence: [`Evidence: ${backend.evidence?.toFixed(2) || '—'}`, `Confidence: ${backend.confidence?.toFixed(2) || '—'}`],
    recommendation: 'Review regional hazard assessment',
    humanAction: 'Pending operator review',
  };
}
