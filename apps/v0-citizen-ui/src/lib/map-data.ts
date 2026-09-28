/**
 * Map data fetching and transformation
 * Connects real backend API data to map layers
 */

const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || 'https://raspberrypi.tail39c545.ts.net';

export interface NodeLocation {
  node_id: string;
  lat: number;
  lon: number;
  status: string;
}

export interface IncidentLocation {
  incident_id: string;
  lat: number;
  lon: number;
  hazard_type?: string;
  state: string;
}

/**
 * Fetch node locations from backend
 * Nodes have real location data (lat/lon)
 */
export async function fetchNodeLocations(): Promise<NodeLocation[]> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/nodes`);

    if (!response.ok) {
      console.error('[MapData] Failed to fetch nodes:', response.status);
      return [];
    }

    const nodes = await response.json();
    console.log('[MapData] Fetched nodes:', nodes.length);

    // Extract nodes with valid location data
    return nodes
      .filter((node: any) => node.location?.lat && node.location?.lon)
      .map((node: any) => ({
        node_id: node.node_id,
        lat: node.location.lat,
        lon: node.location.lon,
        status: node.status,
      }));
  } catch (error) {
    console.error('[MapData] Failed to fetch node locations:', error);
    return [];
  }
}

/**
 * Fetch incident locations from backend
 * Returns only incidents with real centroid data (currently none for test alerts)
 */
export async function fetchIncidentLocations(): Promise<IncidentLocation[]> {
  try {
    const response = await fetch(`${BACKEND_URL}/api/incidents?active_only=true`);

    if (!response.ok) {
      console.error('[MapData] Failed to fetch incidents:', response.status);
      return [];
    }

    const incidents = await response.json();
    console.log('[MapData] Fetched incidents:', incidents.length);

    // Extract incidents with valid centroid data
    // NOTE: Test alerts currently have centroid: null
    return incidents
      .filter((incident: any) => incident.centroid?.lat && incident.centroid?.lon)
      .map((incident: any) => ({
        incident_id: incident.incident_id,
        lat: incident.centroid.lat,
        lon: incident.centroid.lon,
        hazard_type: incident.hazard_assessments?.[0]?.hazard_type,
        state: incident.state,
      }));
  } catch (error) {
    console.error('[MapData] Failed to fetch incident locations:', error);
    return [];
  }
}

/**
 * Get hazard icon for map markers
 */
export function getHazardIcon(hazardType?: string): string {
  const icons: Record<string, string> = {
    fire: '🔥',
    flood: '🌊',
    landslide: '⛰️',
    pollution: '💨',
    heat: '🌡️',
  };

  return icons[hazardType || ''] || '⚠️';
}

/**
 * Get hazard color for map markers
 */
export function getHazardColor(hazardType?: string): string {
  const colors: Record<string, string> = {
    fire: '#e63946',
    flood: '#457b9d',
    landslide: '#6a4c93',
    pollution: '#9b9b9b',
    heat: '#f77f00',
  };

  return colors[hazardType || ''] || '#923d34';
}
