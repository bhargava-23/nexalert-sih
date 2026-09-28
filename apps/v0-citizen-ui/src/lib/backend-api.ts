/**
 * Backend API client for NexAlert Citizen UI
 * Connects to real backend alert and incident endpoints
 */

const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || 'https://raspberrypi.tail39c545.ts.net';

export interface BackendAlert {
  alert_id: string;
  incident_id: string;
  state: string;
  hazard_type: string;
  severity: string | null;
  title: string;
  message: string;
  action_guidance: string | null;
  recommended_at: string;
  approved_at: string | null;
  issued_at: string | null;
  resolved_at: string | null;
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

/**
 * Fetch active citizen alerts from backend
 */
export async function fetchCitizenAlerts(): Promise<BackendAlert[]> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/alerts/citizen?active_only=true`);

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const alerts: BackendAlert[] = await response.json();
    console.log('[BackendAPI] Fetched citizen alerts:', alerts.length);

    return alerts;
  } catch (error) {
    console.error('[BackendAPI] Failed to fetch citizen alerts:', error);
    return [];
  }
}

/**
 * Convert backend alert to Citizen UI EventRecord format
 */
export function alertToEventRecord(alert: BackendAlert): import('@/lib/nexalert-data').EventRecord {
  // Map backend hazard types to UI display
  const hazardDisplayMap: Record<string, string> = {
    fire: 'FIRE',
    flood: 'FLOOD',
    landslide: 'LANDSLIDE',
    pollution: 'AIR QUALITY',
    heat: 'HEAT',
  };

  // Map backend alert state to UI hazard state
  const stateMap: Record<string, 'CONFIRMED' | 'WATCH' | 'RESOLVED' | 'UNKNOWN'> = {
    ISSUED: 'CONFIRMED',
    DELIVERING: 'CONFIRMED',
    DELIVERED: 'CONFIRMED',
    STAND_DOWN: 'RESOLVED',
  };

  // Map backend severity to UI severity
  const severityMap: Record<string, 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'> = {
    CRITICAL: 'CRITICAL',
    WARNING: 'HIGH',
    ADVISORY: 'MODERATE',
  };

  // Calculate freshness based on issued_at timestamp
  const getFreshness = (issuedAt: string | null): 'LIVE' | 'RECENT' | 'STALE' | 'UNKNOWN' => {
    if (!issuedAt) return 'UNKNOWN';

    const now = Date.now();
    const issued = new Date(issuedAt).getTime();
    const ageMinutes = (now - issued) / (1000 * 60);

    if (ageMinutes < 15) return 'LIVE';
    if (ageMinutes < 60) return 'RECENT';
    return 'STALE';
  };

  const hazardType = hazardDisplayMap[alert.hazard_type] || alert.hazard_type.toUpperCase();
  const severity = severityMap[alert.severity || 'WARNING'] || 'MODERATE';
  const state = stateMap[alert.state] || 'UNKNOWN';
  const freshness = getFreshness(alert.issued_at);

  return {
    id: alert.alert_id,
    title: alert.title,
    kind: hazardType,
    state,
    severity,
    summary: alert.message,
    action: alert.action_guidance || 'Follow authority guidance',
    distance: '—',
    direction: 'regional',
    area: 'Regional area',
    updatedAt: alert.issued_at ? new Date(alert.issued_at).toLocaleString() : 'Recently',
    freshness,
    source: 'NexAlert backend',
    evidence: [alert.message],
    operationalNote: alert.action_guidance || '',
  };
}

/**
 * Get the most critical active alert for Citizen home page
 */
export async function getCurrentEmergency(): Promise<import('@/lib/nexalert-data').EventRecord | null> {
  const alerts = await fetchCitizenAlerts();

  if (alerts.length === 0) {
    return null;
  }

  // Find the most critical alert (CRITICAL > HIGH > MODERATE)
  const criticalAlert = alerts.find(a => a.severity === 'CRITICAL');
  const highAlert = alerts.find(a => a.severity === 'WARNING');
  const mostCritical = criticalAlert || highAlert || alerts[0];

  return alertToEventRecord(mostCritical);
}

/**
 * Get fire geometry for an incident (CURRENT/WARNING/PROJECTION zones)
 * Backend-authoritative geometry - DO NOT calculate or generate in frontend
 *
 * CRITICAL: Geometry comes from backend FireSimulation → FireGeometry
 * Frontend ONLY renders the returned GeoJSON, never calculates zones
 */
export async function fetchIncidentGeometry(incidentId: string): Promise<IncidentGeometry | null> {
  try {
    // Note: Geometry endpoint is /api/incidents/{id}/geometries (not under /api/v1)
    const response = await fetch(`${BACKEND_URL}/api/incidents/${incidentId}/geometries`);

    if (!response.ok) {
      if (response.status === 404) {
        console.log('[BackendAPI] No geometry found for incident:', incidentId);
        return null;
      }
      throw new Error(`Backend returned ${response.status}`);
    }

    const geometry: IncidentGeometry = await response.json();
    console.log('[BackendAPI] Fetched incident geometry:', geometry.features?.length || 0, 'zones');

    return geometry;
  } catch (error) {
    console.error('[BackendAPI] Failed to fetch incident geometry:', error);
    return null;
  }
}
