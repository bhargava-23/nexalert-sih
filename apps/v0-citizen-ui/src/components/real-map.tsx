/**
 * RealMap - Real interactive geographic map with browser geolocation
 * Connects to real backend node and incident locations
 */

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, GeoJSON } from 'react-leaflet';
import { LocateFixed, AlertTriangle, MapPin } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchNodeLocations, fetchIncidentLocations, getHazardColor, getHazardIcon, type NodeLocation, type IncidentLocation } from '@/lib/map-data';
import { fetchIncidentGeometry, type IncidentGeometry } from '@/lib/backend-api';

// Fix Leaflet default marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCAyNSA0MSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIuNSAwQzUuNiAwIDAgNS42IDAgMTIuNWMwIDkuNCAxMi41IDI4LjUgMTIuNSAyOC41UzI1IDIxLjkgMjUgMTIuNUMyNSA1LjYgMTkuNCAwIDEyLjUgMHptMCAxN2MtMi41IDAtNC41LTItNC41LTQuNXMyLTQuNSA0LjUtNC41IDQuNSAyIDQuNSA0LjUtMiA0LjUtNC41IDQuNXoiIGZpbGw9IiMxOTVkNTIiLz48L3N2Zz4=',
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjUiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCAyNSA0MSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTIuNSAwQzUuNiAwIDAgNS42IDAgMTIuNWMwIDkuNCAxMi41IDI4LjUgMTIuNSAyOC41UzI1IDIxLjkgMjUgMTIuNUMyNSA1LjYgMTkuNCAwIDEyLjUgMHptMCAxN2MtMi41IDAtNC41LTItNC41LTQuNXMyLTQuNSA0LjUtNC41IDQuNSAyIDQuNSA0LjUtMiA0LjUtNC41IDQuNXoiIGZpbGw9IiMxOTVkNTIiLz48L3N2Zz4=',
  shadowUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDEiIGhlaWdodD0iNDEiIHZpZXdCb3g9IjAgMCA0MSA0MSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZWxsaXBzZSBjeD0iMjAiIGN5PSIzNSIgcng9IjE1IiByeT0iNSIgZmlsbD0iIzAwMCIgb3BhY2l0eT0iMC4zIi8+PC9zdmc+'
});

// Zone styling for backend-authoritative geometry
const getZoneStyle = (zoneType: 'CURRENT' | 'WARNING' | 'PROJECTION') => {
  const styles = {
    CURRENT: { fillColor: '#ef4444', color: '#ef4444', fillOpacity: 0.25, weight: 2 },
    WARNING: { fillColor: '#f59e0b', color: '#f59e0b', fillOpacity: 0.2, weight: 2 },
    PROJECTION: { fillColor: '#fbbf24', color: '#fbbf24', fillOpacity: 0.15, weight: 2 },
  };
  return styles[zoneType];
};

interface UserLocation {
  lat: number;
  lon: number;
}

type LocationState =
  | { status: 'loading' }
  | { status: 'granted'; location: UserLocation }
  | { status: 'denied' }
  | { status: 'unavailable'; error: string }
  | { status: 'timeout' };

// Component to auto-center map on user location
function MapCenterController({ location }: { location: UserLocation | null }) {
  const map = useMap();

  useEffect(() => {
    if (location) {
      map.setView([location.lat, location.lon], 13);
    }
  }, [location, map]);

  return null;
}

export function RealMap() {
  const [locationState, setLocationState] = useState<LocationState>({ status: 'loading' });
  const [retryCount, setRetryCount] = useState(0);
  const [nodes, setNodes] = useState<NodeLocation[]>([]);
  const [incidents, setIncidents] = useState<IncidentLocation[]>([]);
  const [geometries, setGeometries] = useState<Record<string, IncidentGeometry>>({});

  // Fetch node and incident locations from backend
  useEffect(() => {
    const fetchMapData = async () => {
      const [nodeData, incidentData] = await Promise.all([
        fetchNodeLocations(),
        fetchIncidentLocations(),
      ]);

      setNodes(nodeData);
      setIncidents(incidentData);

      console.log('[RealMap] Loaded node locations:', nodeData.length);
      console.log('[RealMap] Loaded incident locations:', incidentData.length);

      // Fetch geometry for each incident (backend-authoritative)
      const newGeometries: Record<string, IncidentGeometry> = {};
      for (const incident of incidentData) {
        const geometry = await fetchIncidentGeometry(incident.incident_id);
        if (geometry) {
          newGeometries[incident.incident_id] = geometry;
          console.log('[RealMap] Loaded geometry for incident:', incident.incident_id, geometry.features.length, 'zones');
        }
      }
      setGeometries(newGeometries);
    };

    fetchMapData();

    // Refresh every 30 seconds
    const interval = setInterval(fetchMapData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Check if geolocation is supported
    if (!navigator.geolocation) {
      setLocationState({
        status: 'unavailable',
        error: 'Geolocation is not supported by your browser'
      });
      return;
    }

    // Request current position
    const timeoutId = setTimeout(() => {
      setLocationState({ status: 'timeout' });
    }, 10000); // 10 second timeout

    navigator.geolocation.getCurrentPosition(
      (position) => {
        clearTimeout(timeoutId);
        setLocationState({
          status: 'granted',
          location: {
            lat: position.coords.latitude,
            lon: position.coords.longitude
          }
        });
      },
      (error) => {
        clearTimeout(timeoutId);
        if (error.code === error.PERMISSION_DENIED) {
          setLocationState({ status: 'denied' });
        } else if (error.code === error.TIMEOUT) {
          setLocationState({ status: 'timeout' });
        } else {
          setLocationState({
            status: 'unavailable',
            error: error.message
          });
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );

    return () => clearTimeout(timeoutId);
  }, [retryCount]);

  const handleRetry = () => {
    setLocationState({ status: 'loading' });
    setRetryCount(prev => prev + 1);
  };

  // Default center (will be overridden when user location loads)
  const defaultCenter: [number, number] = [20.5937, 78.9629]; // India center
  const userLocation = locationState.status === 'granted' ? locationState.location : null;

  return (
    <div data-testid="map-real" className="relative min-h-[280px] overflow-hidden rounded-2xl border border-[#b9c8c5] bg-[#dbe5dc] shadow-[0_10px_28px_rgba(38,61,59,.10)] sm:min-h-[360px]">
      {/* Loading state overlay - only while loading */}
      {locationState.status === 'loading' && (
        <div className="absolute inset-0 z-[1000] flex flex-col items-center justify-center bg-[#dbe5dc]/95 backdrop-blur-sm">
          <div className="mb-3 h-8 w-8 animate-spin rounded-full border-4 border-[#b9c8c5] border-t-[#195d52]" />
          <p className="font-mono-safe text-[11px] font-medium tracking-wide text-[#245b66]">
            REQUESTING LOCATION
          </p>
          <p className="mt-1 text-xs text-[#5a6763]">
            Allow location access to see your position
          </p>
        </div>
      )}

      {/* Map header info */}
      <div className="absolute left-3 top-3 z-[500] max-w-[calc(100%-1.5rem)] rounded-xl border border-[#c1d1cb] bg-[#fff8f4]/95 p-2.5 backdrop-blur-sm">
        <p className="font-mono-safe text-[10px] tracking-[.14em] text-[#245b66]">
          {userLocation ? 'YOUR LOCATION · LIVE MAP' : 'CITIZEN MAP · LIVE'}
        </p>
        {userLocation && (
          <p className="mt-1 font-mono text-[9px] text-[#5a6763]">
            {userLocation.lat.toFixed(5)}°N, {userLocation.lon.toFixed(5)}°E
          </p>
        )}
        {locationState.status === 'denied' && (
          <p className="mt-1 text-[9px] text-[#923d34]">
            Location access denied
          </p>
        )}
      </div>

      {/* Center button - only if location available */}
      {userLocation && (
        <button
          type="button"
          onClick={() => {
            // Re-center map on user location
            const event = new CustomEvent('recenter-map');
            window.dispatchEvent(event);
          }}
          data-testid="button-map-center"
          className="absolute right-3 top-3 z-[500] flex h-10 w-10 items-center justify-center rounded-xl border border-[#b9c8c5] bg-[#fff8f4]/95 text-[#245b66] shadow-sm hover:bg-[#e3f1ec]"
          aria-label="Center map on my location"
        >
          <LocateFixed size={18} />
        </button>
      )}

      {/* Map scale */}
      <div className="absolute bottom-3 left-3 z-[500] rounded-lg bg-[#fff8f4]/90 px-2.5 py-2 font-mono-safe text-[9px] text-[#5a6763] backdrop-blur-sm">
        <span>OPENSTREETMAP TILES</span>
      </div>

      {/* Leaflet Map - always renders */}
      <MapContainer
        center={userLocation ? [userLocation.lat, userLocation.lon] : defaultCenter}
        zoom={userLocation ? 13 : 5}
        className="h-full w-full"
        style={{ minHeight: '280px', background: !navigator.onLine ? '#e3f1ec' : undefined }}
        zoomControl={false}
      >
        {/* Offline local fallback for base map */}
        {!navigator.onLine && (
           <div className="absolute inset-0 z-0 flex items-center justify-center opacity-30 pointer-events-none">
              <span className="font-mono text-4xl text-[#195d52]">OFFLINE LOCAL MAP</span>
           </div>
        )}
        {navigator.onLine && (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}

        {/* User location marker - only if available */}
        {userLocation && (
          <Marker
            position={[userLocation.lat, userLocation.lon]}
            icon={L.divIcon({
              className: '',
              html: `
                <div style="
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  width: 36px;
                  height: 36px;
                  border-radius: 50%;
                  background: #195d52;
                  border: 4px solid #fff8f4;
                  box-shadow: 0 4px 12px rgba(25, 93, 82, 0.4);
                ">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff8f4" stroke-width="2.5">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                </div>
              `,
              iconSize: [36, 36],
              iconAnchor: [18, 18]
            })}
          >
            <Popup>
              <div className="text-center">
                <p className="font-mono-safe text-[9px] font-medium tracking-wide text-[#195d52]">
                  YOUR LOCATION
                </p>
                <p className="mt-1 text-xs text-[#5a6763]">
                  {userLocation.lat.toFixed(5)}°N<br />
                  {userLocation.lon.toFixed(5)}°E
                </p>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Node location markers - real backend data */}
        {nodes.map((node) => (
          <Marker
            key={node.node_id}
            position={[node.lat, node.lon]}
            icon={L.divIcon({
              className: '',
              html: `
                <div style="
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  width: 28px;
                  height: 28px;
                  border-radius: 50%;
                  background: #457b9d;
                  border: 3px solid #fff8f4;
                  box-shadow: 0 2px 8px rgba(69, 123, 157, 0.4);
                ">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff8f4" stroke-width="2.5">
                    <rect x="4" y="4" width="16" height="16" rx="2"/>
                    <circle cx="12" cy="12" r="2"/>
                  </svg>
                </div>
              `,
              iconSize: [28, 28],
              iconAnchor: [14, 14]
            })}
          >
            <Popup>
              <div className="text-center">
                <p className="font-mono-safe text-[9px] font-medium tracking-wide text-[#457b9d]">
                  SENSOR NODE
                </p>
                <p className="mt-1 text-xs font-medium text-[#5a6763]">
                  {node.node_id}
                </p>
                <p className="text-[10px] text-[#5a6763]">
                  Status: {node.status}
                </p>
                <p className="text-[9px] text-[#7a8783]">
                  {node.lat.toFixed(5)}°N, {node.lon.toFixed(5)}°E
                </p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Incident location markers - only when backend provides centroid */}
        {incidents.map((incident) => (
          <Marker
            key={incident.incident_id}
            position={[incident.lat, incident.lon]}
            icon={L.divIcon({
              className: '',
              html: `
                <div style="
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  width: 40px;
                  height: 40px;
                  border-radius: 50%;
                  background: ${getHazardColor(incident.hazard_type)};
                  border: 4px solid #fff8f4;
                  box-shadow: 0 4px 16px rgba(230, 57, 70, 0.5);
                ">
                  <span style="font-size: 20px; line-height: 1;">
                    ${getHazardIcon(incident.hazard_type)}
                  </span>
                </div>
              `,
              iconSize: [40, 40],
              iconAnchor: [20, 20]
            })}
          >
            <Popup>
              <div className="text-center">
                <p className="font-mono-safe text-[9px] font-medium tracking-wide" style={{ color: getHazardColor(incident.hazard_type) }}>
                  HAZARD DETECTED
                </p>
                <p className="mt-1 text-xs font-bold text-[#5a6763]">
                  {incident.hazard_type?.toUpperCase() || 'UNKNOWN'}
                </p>
                <p className="text-[10px] text-[#5a6763]">
                  State: {incident.state}
                </p>
                <p className="text-[9px] text-[#7a8783]">
                  {incident.lat.toFixed(5)}°N, {incident.lon.toFixed(5)}°E
                </p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Backend-authoritative fire geometry (CURRENT/WARNING/PROJECTION zones) */}
        {Object.entries(geometries).flatMap(([incidentId, geometry]) =>
          geometry.features.map((feature, idx) => (
            <GeoJSON
              key={`geometry-${incidentId}-${idx}-${feature.properties.zone_type}`}
              data={feature}
              style={getZoneStyle(feature.properties.zone_type)}
            />
          ))
        )}

        {/* Auto-center controller */}
        {userLocation && <MapCenterController location={userLocation} />}
      </MapContainer>
    </div>
  );
}
