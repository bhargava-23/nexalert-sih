import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, GeoJSON, useMap } from 'react-leaflet';
import { Eye, EyeOff, Layers3, Siren, Target, WifiOff } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Node, Incident, SOSRequest } from '@/types';
import type { IncidentGeometry } from '@/lib/api';
import { useIncidentGeometry } from '@/lib/hooks';

// Fix Leaflet default marker icons
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

type Selection = { kind: 'node'; value: Node } | { kind: 'incident'; value: Incident } | { kind: 'sos'; value: SOSRequest } | null;

interface MapLayer {
  id: string;
  name: string;
  description: string;
  visible: boolean;
  icon: 'map' | 'nodes' | 'risk' | 'sos' | 'terrain';
}

// Default map layers
const defaultLayers: MapLayer[] = [
  { id: 'base', name: 'Base map', description: 'OpenStreetMap base layer', visible: true, icon: 'map' },
  { id: 'nodes', name: 'Field nodes', description: 'Sensor nodes and relay infrastructure', visible: true, icon: 'nodes' },
  { id: 'incidents', name: 'Incidents', description: 'Active incident markers', visible: true, icon: 'sos' },
  { id: 'links', name: 'Network links', description: 'Master-slave logical connections', visible: true, icon: 'terrain' },
];

// Custom node marker
const createNodeIcon = (state: string) => {
  const color = state === 'ONLINE' ? '#10b981' : state === 'DEGRADED' ? '#f59e0b' : '#ef4444';
  return L.divIcon({
    className: 'custom-node-marker',
    html: `<div style="background: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
};

// Custom incident marker
const createIncidentIcon = () => {
  return L.divIcon({
    className: 'custom-incident-marker',
    html: `<div style="background: #ef4444; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">!</div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

// Zone styling for backend-authoritative geometry
const getZoneStyle = (zoneType: 'CURRENT' | 'WARNING' | 'PROJECTION') => {
  const styles = {
    CURRENT: { fillColor: '#ef4444', color: '#ef4444', fillOpacity: 0.25, weight: 2 },
    WARNING: { fillColor: '#f59e0b', color: '#f59e0b', fillOpacity: 0.2, weight: 2 },
    PROJECTION: { fillColor: '#fbbf24', color: '#fbbf24', fillOpacity: 0.15, weight: 2 },
  };
  return styles[zoneType];
};

// Map bounds updater
function MapBounds({ nodes }: { nodes: Node[] }) {
  const map = useMap();

  useEffect(() => {
    if (nodes.length > 0) {
      const bounds = L.latLngBounds(nodes.map(n => [n.coordinates[0], n.coordinates[1]]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
    }
  }, [nodes, map]);

  return null;
}

export function MapSurface({
  compact = false,
  nodes = [],
  incidents = [],
  sos = [],
  masterLocation,
  onSelection,
  selectedIncidentId
}: {
  compact?: boolean;
  nodes?: Node[];
  incidents?: Incident[];
  sos?: SOSRequest[];
  masterLocation?: [number, number] | null;
  onSelection?: (selection: Selection) => void;
  selectedIncidentId?: string | null;
}) {
  const [layers, setLayers] = useState<MapLayer[]>(defaultLayers);
  const [selected, setSelected] = useState<Selection>(null);
  const [showLegend, setShowLegend] = useState(false);

  const visible = (id: string) => layers.find((layer) => layer.id === id)?.visible !== false;
  const choose = (selection: Selection) => {
    setSelected(selection);
    onSelection?.(selection);
  };

  // Fetch backend-authoritative geometry for selected incident
  const { data: geometry, isLoading: geometryLoading } = useIncidentGeometry(selectedIncidentId);

  // Debug: Log nodes data
  console.log('[MapSurface] Nodes received:', nodes?.length || 0);
  if (nodes && nodes.length > 0) {
    console.log('[MapSurface] First node coordinates:', nodes[0].coordinates);
  }

  // Default center (Bangalore area as fallback, or first node)
  const center: [number, number] = nodes.length > 0
    ? nodes[0].coordinates
    : [13.13495, 77.56681]; // NODE-001 default location

  console.log('[MapSurface] Map center:', center);

  return (
    <div className={`relative ${compact ? 'h-[360px]' : 'h-[530px]'} w-full`} data-testid="map-operational-surface">
      <MapContainer
        center={center}
        zoom={13}
        className="h-full w-full"
        style={{ background: '#1e293b' }}
      >
        {visible('base') && (
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}

        {/* Auto-fit bounds to nodes */}
        {nodes.length > 0 && <MapBounds nodes={nodes} />}

        {/* Network links (Master → Node connections) */}
        {visible('links') && masterLocation && nodes.map((node) => (
          <Polyline
            key={`link-${node.id}`}
            positions={[masterLocation, node.coordinates]}
            color="#64748b"
            weight={1}
            dashArray="4 4"
            opacity={0.6}
          />
        ))}

        {/* Field nodes */}
        {visible('nodes') && nodes.map((node) => (
          <Marker
            key={node.id}
            position={node.coordinates}
            icon={createNodeIcon(node.state)}
            eventHandlers={{
              click: () => choose({ kind: 'node', value: node }),
            }}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-bold">{node.name}</div>
                <div className="text-xs text-slate-600 mt-1">
                  <div>{node.location} · {node.kind}</div>
                  <div className={node.state === 'ONLINE' ? 'text-emerald-600' : 'text-amber-600'}>
                    {node.state} · {node.lastSeen}
                  </div>
                  <div>Battery {node.battery}% · {node.signal}</div>
                  <div className="text-slate-400 mt-1">
                    {node.coordinates[0].toFixed(5)}°N, {node.coordinates[1].toFixed(5)}°E
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Master location marker */}
        {masterLocation && (
          <Marker position={masterLocation}>
            <Popup>
              <div className="text-sm">
                <div className="font-bold">Master Coordination</div>
                <div className="text-xs text-slate-600">
                  {masterLocation[0].toFixed(5)}°N, {masterLocation[1].toFixed(5)}°E
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Incidents */}
        {visible('incidents') && incidents.map((incident) => {
          // Use first node location as fallback for incident location
          const position: [number, number] = nodes.length > 0 ? nodes[0].coordinates : center;
          return (
            <Marker
              key={incident.id}
              position={position}
              icon={createIncidentIcon()}
              eventHandlers={{
                click: () => choose({ kind: 'incident', value: incident }),
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-bold">{incident.title}</div>
                  <div className="text-xs text-slate-600 mt-1">
                    <div>{incident.id} · {incident.location}</div>
                    <div className="text-red-600">{incident.state} · {incident.severity}</div>
                    <div>Freshness: {incident.freshness}</div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* SOS markers */}
        {visible('sos') && sos.filter((item) => item.state !== 'RESOLVED').map((item, index) => {
          // Offset SOS markers slightly from center
          const offset = 0.01;
          const sosPosition: [number, number] = [
            center[0] + (offset * (index - 1)),
            center[1] + (offset * (index - 1))
          ];
          return (
            <Marker
              key={item.id}
              position={sosPosition}
              eventHandlers={{
                click: () => choose({ kind: 'sos', value: item }),
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-bold">{item.id} · {item.caller}</div>
                  <div className="text-xs text-slate-600 mt-1">
                    <div>{item.location}</div>
                    <div className="text-amber-600">{item.state} · {item.channel}</div>
                    <div className="mt-1">{item.note}</div>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}

        {/* Backend-authoritative fire geometry (CURRENT/WARNING/PROJECTION zones) */}
        {geometry && geometry.features && geometry.features.map((feature, idx) => (
          <GeoJSON
            key={`geometry-${idx}-${feature.properties.zone_type}`}
            data={feature}
            style={getZoneStyle(feature.properties.zone_type)}
          />
        ))}
      </MapContainer>

      {/* Map controls overlay */}
      <div className="absolute left-3 top-3 z-[1000] flex items-center gap-2 rounded-md border border-slate-300/10 bg-[#0c1b24]/85 px-2.5 py-2 text-[10px] text-slate-300 backdrop-blur-sm">
        <Target size={13} className="text-cyan-300" />
        <span className="font-mono">
          {center[0].toFixed(4)}° N, {center[1].toFixed(4)}° E
        </span>
        <span className="text-slate-600">·</span>
        <span>{new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })} IST</span>
      </div>

      {/* Layer controls */}
      <div className="absolute bottom-3 left-3 z-[1000] flex max-w-[calc(100%-24px)] items-center gap-1.5 overflow-x-auto rounded-md border border-slate-300/10 bg-[#0c1b24]/90 p-1.5 backdrop-blur-sm">
        <button
          type="button"
          className={`button-compact !border-0 !py-1.5 !text-[10px] ${showLegend ? '!bg-cyan-300/10 !text-cyan-200' : ''}`}
          onClick={() => setShowLegend((value) => !value)}
          data-testid="button-toggle-map-legend"
        >
          <Layers3 size={13} />Legend
        </button>
        {layers.map((layer) => (
          <button
            key={layer.id}
            type="button"
            className={`button-compact !border-0 !bg-transparent !py-1.5 !text-[10px] ${layer.visible ? 'text-slate-200' : 'text-slate-600'}`}
            onClick={() => setLayers((current) => current.map((item) => item.id === layer.id ? { ...item, visible: !item.visible } : item))}
            title={layer.description}
            data-testid={`button-toggle-layer-${layer.id}`}
          >
            {layer.visible ? <Eye size={12} /> : <EyeOff size={12} />} {layer.name}
          </button>
        ))}
      </div>

      {/* Legend panel */}
      {showLegend && (
        <div className="absolute bottom-16 left-3 z-[1000] w-56 rounded-md border border-slate-300/15 bg-[#0c1b24]/95 p-3 shadow-2xl backdrop-blur-sm" data-testid="map-legend">
          <div className="eyebrow mb-2">Map symbology</div>
          <div className="space-y-2 text-[10px] text-slate-300">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-emerald-500 border-2 border-white" />
              <span>Node online</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-amber-500 border-2 border-white" />
              <span>Node degraded</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-red-500 border-2 border-white" />
              <span>Node offline/unreachable</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-4 w-4 rounded-full bg-red-500 border-2 border-white flex items-center justify-center text-white text-[10px]">!</span>
              <span>Active incident</span>
            </div>
            <div className="mt-2 border-t border-slate-800 pt-2 text-[9px] text-slate-500">
              Real-time geographic display. Network links show Master→Node topology. SOS markers approximate.
            </div>
          </div>
        </div>
      )}

      {/* Selection panel */}
      {selected && (
        <div className="absolute right-3 top-16 z-[1000] w-64 rounded-md border border-slate-300/15 bg-[#0c1b24]/95 p-3 shadow-2xl backdrop-blur-sm" data-testid="map-context-panel">
          <div className="mb-1 flex items-center justify-between gap-3">
            <span className="eyebrow">
              {selected.kind === 'node' ? 'Field node' : selected.kind === 'incident' ? 'Incident marker' : 'Citizen SOS'}
            </span>
            <button
              type="button"
              aria-label="Close map context"
              className="text-slate-500 hover:text-slate-100"
              onClick={() => choose(null)}
              data-testid="button-close-map-context"
            >
              ×
            </button>
          </div>
          <div className="text-[12px] font-bold text-slate-100">
            {selected.kind === 'node' ? selected.value.name : selected.kind === 'incident' ? selected.value.title : selected.value.caller}
          </div>
          {selected.kind === 'node' && (
            <div className="mt-2 space-y-1 text-[10px] text-slate-400">
              <div>{selected.value.location} · {selected.value.kind}</div>
              <div className={selected.value.state === 'ONLINE' ? 'text-emerald-300' : 'text-amber-300'}>
                {selected.value.state} · last seen {selected.value.lastSeen}
              </div>
              <div>Battery {selected.value.battery}% · {selected.value.signal}</div>
              <div className="text-slate-500 mt-1">
                {selected.value.coordinates[0].toFixed(5)}°N, {selected.value.coordinates[1].toFixed(5)}°E
              </div>
            </div>
          )}
          {selected.kind === 'incident' && (
            <div className="mt-2 space-y-1 text-[10px] text-slate-400">
              <div>{selected.value.id} · {selected.value.location}</div>
              <div className="text-red-300">{selected.value.state} · {selected.value.severity}</div>
              <div>Freshness {selected.value.freshness}</div>
            </div>
          )}
          {selected.kind === 'sos' && (
            <div className="mt-2 space-y-1 text-[10px] text-slate-400">
              <div>{selected.value.id} · {selected.value.location}</div>
              <div className="text-amber-300">{selected.value.state} · {selected.value.channel}</div>
              <div>{selected.value.note}</div>
            </div>
          )}
          <button
            type="button"
            className="button-compact mt-3 w-full !py-1.5 !text-[10px]"
            onClick={() => choose(null)}
            data-testid="button-dismiss-map-context"
          >
            Keep map open
          </button>
        </div>
      )}

      {/* Empty state */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 z-[999] flex items-center justify-center bg-slate-900/50 backdrop-blur-sm">
          <div className="text-center text-slate-400 p-6">
            <WifiOff size={32} className="mx-auto mb-2 opacity-50" />
            <div className="text-sm font-semibold">No field nodes available</div>
            <div className="text-xs mt-1">Waiting for backend node data...</div>
          </div>
        </div>
      )}
    </div>
  );
}
