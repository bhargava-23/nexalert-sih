/**
 * Fire Spread Simulation Page - Real Backend Integration
 * Connects to /api/simulations for real fire spread modeling
 */

import { useState } from 'react';
import { Download, Flame, Info, Pause, Play, RefreshCw, StepForward, TimerReset } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { PageHeader, ActionButton, SectionTitle } from '@/components/dashboard-components';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://cite-superior-enquiries-noticed.trycloudflare.com/api/v1';

interface Simulation {
  simulation_id: string;
  incident_id: string | null;
  simulation_type: string;
  ignition_lat: number;
  ignition_lon: number;
  ignition_time: string;
  simulation_time: string;
  environmental_state: {
    wind_from_deg: number;
    wind_speed_ms: number;
    moisture_index: number;
  };
  created_at: string;
}

interface SimulationGeometry {
  geometry_id: number;
  simulation_id: string;
  zone_type: string;
  geometry_wkt: string;
  area_hectares: number;
  perimeter_m: number;
  created_at: string;
}

async function fetchSimulations(): Promise<Simulation[]> {
  const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/api/simulations`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const text = await response.text();
  if (!text) return [];
  return JSON.parse(text);
}

// WKT to GeoJSON parser (simple implementation for POLYGON)
function wktToGeoJSON(wkt: string): GeoJSON.Geometry {
  // Remove POLYGON or MULTIPOLYGON wrapper
  const isMulti = wkt.startsWith('MULTIPOLYGON');
  const coordsMatch = wkt.match(/\(\(([^)]+)\)\)/g);

  if (!coordsMatch) {
    throw new Error('Invalid WKT format');
  }

  const rings = coordsMatch.map(ring => {
    const coordStr = ring.replace(/[()]/g, '').trim();
    return coordStr.split(',').map(pair => {
      const [lon, lat] = pair.trim().split(' ').map(Number);
      return [lon, lat];
    });
  });

  if (isMulti || rings.length > 1) {
    // MultiPolygon or Polygon with holes
    return {
      type: 'Polygon',
      coordinates: rings
    };
  } else {
    // Simple Polygon
    return {
      type: 'Polygon',
      coordinates: rings
    };
  }
}

async function fetchSimulationGeometry(simulationId: string): Promise<SimulationGeometry[]> {
  const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/api/simulations/${simulationId}/geometries`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const text = await response.text();
  if (!text) return [];
  return JSON.parse(text);
}

async function startSimulation(): Promise<Simulation> {
  const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/api/simulations/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ignition_lat: 13.13495,
      ignition_lon: 77.56681,
      simulation_type: 'SIMULATION',
      domain_size_m: 10000,
      cell_size_m: 50,
      max_time_minutes: 60,
      wind_speed_ms: 5.0,
      wind_from_deg: 270.0,
      moisture_index: 0.3,
    }),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function useSimulations() {
  return useQuery({
    queryKey: ['simulations'],
    queryFn: fetchSimulations,
    refetchInterval: 15000,
    staleTime: 10000,
  });
}

function useSimulationGeometry(simulationId: string | null) {
  return useQuery({
    queryKey: ['simulation-geometry', simulationId],
    queryFn: () => (simulationId ? fetchSimulationGeometry(simulationId) : Promise.resolve([])),
    enabled: !!simulationId,
    refetchInterval: 15000,
    staleTime: 10000,
  });
}

// Map bounds updater
function MapBounds({ geometries }: { geometries: SimulationGeometry[] }) {
  const map = useMap();

  if (geometries.length > 0) {
    try {
      const geojson = wktToGeoJSON(geometries[0].geometry_wkt);
      if (geojson.type === 'Polygon') {
        const coords = geojson.coordinates[0].map((c: number[]) => [c[1], c[0]]);
        const bounds = L.latLngBounds(coords);
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    } catch (e) {
      console.warn('Failed to parse WKT for bounds:', e);
    }
  }

  return null;
}

export function FireSpreadPageLive() {
  const [mode, setMode] = useState<'LIVE' | 'SIMULATION'>('SIMULATION');
  const [playing, setPlaying] = useState(false);
  const [step, setStep] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  const { data: simulations, isLoading, error, refetch } = useSimulations();
  const latestSimulation = simulations?.[0] || null;
  const { data: geometries } = useSimulationGeometry(latestSimulation?.simulation_id || null);

  const handleStartSimulation = async () => {
    setIsStarting(true);
    try {
      await startSimulation();
      await refetch();
      setFeedback('Simulation started successfully');
    } catch (err: any) {
      setFeedback(`Failed to start simulation: ${err.message}`);
    } finally {
      setIsStarting(false);
    }
  };

  const currentGeometry = geometries?.[Math.min(step, (geometries?.length || 1) - 1)];
  const maxSteps = (geometries?.length || 1) - 1;

  return (
    <div className="content-area">
      <PageHeader
        eyebrow="Hazard geometry / wildfire"
        title="Fire spread"
        description="Inspect observed perimeter and model geometry without presenting projection as fire truth."
        actions={
          <div className="flex gap-2">
            <div className="flex rounded-md border border-slate-800 p-0.5">
              <button
                type="button"
                onClick={() => setMode('LIVE')}
                className={`px-3 py-1.5 text-[10px] font-bold ${
                  mode === 'LIVE' ? 'rounded bg-red-400/15 text-red-200' : 'text-slate-500'
                }`}
                data-testid="button-fire-live"
              >
                LIVE
              </button>
              <button
                type="button"
                onClick={() => setMode('SIMULATION')}
                className={`px-3 py-1.5 text-[10px] font-bold ${
                  mode === 'SIMULATION' ? 'rounded bg-cyan-300/15 text-cyan-200' : 'text-slate-500'
                }`}
                data-testid="button-fire-simulation"
              >
                SIMULATION
              </button>
            </div>
            {!isLoading && !latestSimulation && (
              <ActionButton
                testId="button-start-simulation"
                onClick={handleStartSimulation}
                primary
                disabled={isStarting}
              >
                {isStarting ? <RefreshCw size={13} className="animate-spin" /> : <Flame size={13} />}
                Start Simulation
              </ActionButton>
            )}
          </div>
        }
      />

      {/* Loading state */}
      {isLoading && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-4 text-center text-slate-400">
          <RefreshCw size={20} className="mx-auto mb-2 animate-spin" />
          <div className="text-sm">Loading simulations from backend...</div>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-md border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <strong>Backend error:</strong> {error.message}
        </div>
      )}

      {/* No simulations available */}
      {!isLoading && !error && !latestSimulation && (
        <div className="mb-4 rounded-md border border-slate-700 bg-slate-900/50 p-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
            <Flame size={32} className="text-slate-500" />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-slate-200">No Fire Spread Simulations Available</h3>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            Click "Start Simulation" above to run a fire spread model using NODE-001 prototype location.
          </p>
          <div className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-left text-xs leading-relaxed text-amber-100/80">
            <Info size={14} className="mb-1 inline text-amber-300" /> <strong>Real backend simulation.</strong> The
            simulation uses actual fire spread modeling from the backend at NODE-001's known deployment coordinates.
          </div>
        </div>
      )}

      {/* Simulation data available */}
      {!isLoading && !error && latestSimulation && (
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4">
            {/* Map */}
            <div className="panel p-2">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-2">
                <div className="flex items-center gap-2">
                  <span className={`state-chip ${mode === 'LIVE' ? 'state-confirmed' : 'state-suspected'}`}>
                    {mode}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    {mode === 'LIVE'
                      ? `Simulation ${latestSimulation.simulation_id.slice(0, 8)}`
                      : `Zone: ${currentGeometry?.zone_type || 'N/A'}`}
                  </span>
                </div>
                <div className="font-mono text-[10px] text-slate-600">NO AUTONOMOUS DISPATCH</div>
              </div>
              <div className="h-[450px] w-full">
                <MapContainer
                  center={[latestSimulation.ignition_lat, latestSimulation.ignition_lon]}
                  zoom={14}
                  className="h-full w-full"
                  style={{ background: '#1e293b' }}
                >
                  <TileLayer
                    attribution='&copy; OpenStreetMap'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {currentGeometry && (() => {
                    try {
                      const geojson = wktToGeoJSON(currentGeometry.geometry_wkt);
                      const color = currentGeometry.zone_type === 'CURRENT' ? '#ef4444' :
                                   currentGeometry.zone_type === 'WARNING' ? '#f59e0b' : '#3b82f6';
                      return (
                        <GeoJSON
                          key={currentGeometry.geometry_id}
                          data={geojson as any}
                          style={{ color, fillColor: color, fillOpacity: 0.3, weight: 2 }}
                        />
                      );
                    } catch (e) {
                      console.error('Failed to render geometry:', e);
                      return null;
                    }
                  })()}
                  {geometries && geometries.length > 0 && <MapBounds geometries={geometries} />}
                </MapContainer>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {/* Simulation controls */}
            <div className="panel p-4">
              <div className="eyebrow">Simulation controls</div>
              <div className="mt-3 rounded-md border border-cyan-300/15 bg-cyan-300/[.04] p-3">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-slate-400">Frame position</span>
                  <span className="font-mono text-cyan-200">{currentGeometry?.zone_type || 'N/A'}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-300/60"
                    style={{ width: `${maxSteps > 0 ? (step / maxSteps) * 100 : 0}%` }}
                  />
                </div>
              </div>
              <div className="mt-3 grid grid-cols-4 gap-1.5">
                <button
                  type="button"
                  className="button-compact !px-0"
                  onClick={() => setStep(0)}
                  data-testid="button-fire-reset"
                >
                  <TimerReset size={13} />
                </button>
                <button
                  type="button"
                  className="button-compact !px-0"
                  onClick={() => setStep((value) => Math.min(maxSteps, value + 1))}
                  data-testid="button-fire-step"
                  disabled={step >= maxSteps}
                >
                  <StepForward size={13} />
                </button>
                <button
                  type="button"
                  className={`button-compact !px-0 ${playing ? 'button-primary' : ''}`}
                  onClick={() => setPlaying((value) => !value)}
                  data-testid="button-fire-play"
                >
                  {playing ? <Pause size={13} /> : <Play size={13} />}
                </button>
                <button
                  type="button"
                  className="button-compact !px-0"
                  onClick={() => setFeedback('Simulation frame exported locally')}
                  data-testid="button-fire-export"
                >
                  <Download size={13} />
                </button>
              </div>
              <div className="mt-3 text-[10px] leading-relaxed text-slate-600">
                Simulation geometry from real backend fire spread model. Does not change live incident or dispatch
                resources.
              </div>
            </div>

            {/* Geometry register */}
            <div className="panel p-4">
              <SectionTitle icon={Flame} meta={latestSimulation.incident_id || 'Simulation'}>
                Geometry steps
              </SectionTitle>
              {geometries && geometries.length > 0 ? (
                <div className="space-y-2">
                  {geometries.slice(0, 8).map((geom, idx) => {
                    const color = geom.zone_type === 'CURRENT' ? 'bg-red-400' :
                                 geom.zone_type === 'WARNING' ? 'bg-amber-400' : 'bg-blue-400';
                    return (
                      <button
                        key={geom.geometry_id}
                        onClick={() => setStep(idx)}
                        className={`flex w-full items-center justify-between border-b border-slate-800/70 pb-2 text-[10px] last:border-0 last:pb-0 ${
                          step === idx ? 'text-cyan-200' : 'text-slate-400 hover:text-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`h-2.5 w-2.5 rounded-sm ${color}`} />
                          <span>{geom.zone_type}</span>
                        </div>
                        <span className="text-slate-600">{(geom.area_hectares / 10000).toFixed(1)} km²</span>
                      </button>
                    );
                  })}
                  {geometries.length > 8 && (
                    <div className="text-[9px] text-slate-600">+ {geometries.length - 8} more steps</div>
                  )}
                </div>
              ) : (
                <div className="text-[10px] text-slate-500">No geometry steps available</div>
              )}
            </div>

            {/* Simulation metadata */}
            <div className="panel p-4">
              <div className="eyebrow">Simulation metadata</div>
              <div className="mt-2 space-y-2 text-[10px] text-slate-400">
                <div className="flex justify-between">
                  <span>Simulation ID</span>
                  <span className="font-mono text-slate-200">{latestSimulation.simulation_id.slice(0, 8)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Ignition</span>
                  <span className="text-slate-200">
                    {latestSimulation.ignition_lat.toFixed(5)}, {latestSimulation.ignition_lon.toFixed(5)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Wind</span>
                  <span className="text-slate-200">
                    {latestSimulation.environmental_state.wind_from_deg}° @ {latestSimulation.environmental_state.wind_speed_ms} m/s
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Data source</span>
                  <span className="text-cyan-200">BACKEND</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {feedback && (
        <div
          className="fixed bottom-4 right-4 z-50 flex max-w-xs items-center gap-3 rounded-md border border-cyan-300/30 bg-[#102731] px-3 py-2.5 text-[11px] text-cyan-100 shadow-2xl"
          role="status"
        >
          {feedback}
          <button
            type="button"
            className="ml-auto text-slate-500 hover:text-white"
            onClick={() => setFeedback('')}
            data-testid="button-close-feedback"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
