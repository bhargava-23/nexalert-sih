/**
 * React Query hooks for NexAlert backend data fetching
 */

import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { api, type BackendNode, type BackendTelemetry, type BackendHazard, type BackendIncident, type BackendRegionalHazard, type IncidentGeometry } from './api';
import { transformNode, transformTelemetry, transformRegionalHazard, type Node, type TelemetryRecord, type Incident } from '@/types';

/**
 * Fetch all nodes from backend
 * Refetch every 10 seconds
 */
export function useNodes(): UseQueryResult<Node[], Error> {
  return useQuery({
    queryKey: ['nodes'],
    queryFn: async () => {
      const backendNodes = await api.getNodes();
      return backendNodes.map(transformNode);
    },
    refetchInterval: 10000, // 10 seconds
    staleTime: 5000,
  });
}

/**
 * Fetch latest telemetry from all nodes
 * Refetch every 5 seconds for live updates
 */
export function useLatestTelemetry(): UseQueryResult<TelemetryRecord[], Error> {
  return useQuery({
    queryKey: ['telemetry', 'latest'],
    queryFn: async () => {
      const backendTelemetry = await api.getLatestTelemetry();
      return backendTelemetry.map(transformTelemetry);
    },
    refetchInterval: 5000, // 5 seconds for live telemetry
    staleTime: 2000,
  });
}

/**
 * Fetch telemetry history for a specific node
 */
export function useNodeTelemetry(nodeId: string, limit: number = 100): UseQueryResult<TelemetryRecord[], Error> {
  return useQuery({
    queryKey: ['telemetry', nodeId, limit],
    queryFn: async () => {
      const backendTelemetry = await api.getNodeTelemetry(nodeId, limit);
      return backendTelemetry.map(transformTelemetry);
    },
    refetchInterval: 10000,
    enabled: !!nodeId,
  });
}

/**
 * Fetch all hazard assessments
 */
export function useHazards(): UseQueryResult<BackendHazard[], Error> {
  return useQuery({
    queryKey: ['hazards'],
    queryFn: () => api.getHazards(),
    refetchInterval: 10000,
  });
}

/**
 * Fetch hazard assessments for a specific node
 */
export function useNodeHazards(nodeId: string): UseQueryResult<BackendHazard[], Error> {
  return useQuery({
    queryKey: ['hazards', nodeId],
    queryFn: () => api.getNodeHazards(nodeId),
    refetchInterval: 10000,
    enabled: !!nodeId,
  });
}

/**
 * Fetch all incidents (Track B2)
 */
export function useIncidents(): UseQueryResult<BackendIncident[], Error> {
  return useQuery({
    queryKey: ['incidents'],
    queryFn: () => api.getIncidents(),
    refetchInterval: 15000, // 15 seconds
  });
}

/**
 * Fetch regional hazard assessments (Track B2)
 * Transform to frontend incident format
 */
export function useRegionalHazards(): UseQueryResult<Incident[], Error> {
  return useQuery({
    queryKey: ['regional-hazards'],
    queryFn: async () => {
      const backendRegional = await api.getRegionalHazards();
      return backendRegional.map(transformRegionalHazard);
    },
    refetchInterval: 15000,
  });
}

/**
 * Fetch backend-authoritative fire geometry for an incident
 * Returns GeoJSON FeatureCollection with CURRENT/WARNING/PROJECTION zones
 *
 * CRITICAL: This is READ-ONLY rendering of backend geometry
 * Frontend NEVER calculates, approximates, or generates geometry zones
 * Backend FireSimulation → FireGeometry is the single source of truth
 */
export function useIncidentGeometry(incidentId: string | null): UseQueryResult<IncidentGeometry, Error> {
  return useQuery({
    queryKey: ['incident-geometry', incidentId],
    queryFn: () => api.getIncidentGeometry(incidentId!),
    enabled: !!incidentId, // Only fetch when we have a valid incident ID
    refetchInterval: 30000, // 30 seconds - geometry updates less frequently
    staleTime: 20000,
  });
}

/**
 * Fetch API health status
 */
export function useHealth(): UseQueryResult<{ status: string; timestamp: string; database: string }, Error> {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.getHealth(),
    refetchInterval: 30000, // 30 seconds
  });
}

/**
 * Combined hook for overview page metrics
 */
export function useOverviewMetrics() {
  const { data: nodes, isLoading: nodesLoading, error: nodesError } = useNodes();
  const { data: incidents, isLoading: incidentsLoading } = useRegionalHazards();
  const { data: hazards, isLoading: hazardsLoading } = useHazards();

  const isLoading = nodesLoading || incidentsLoading || hazardsLoading;

  // Calculate metrics from real data
  const activeIncidents = incidents?.filter(i => i.state !== 'RESOLVED').length || 0;
  const confirmedIncidents = incidents?.filter(i => i.state === 'CONFIRMED').length || 0;
  const watchIncidents = incidents?.filter(i => i.state === 'WATCH').length || 0;
  const suspectedIncidents = incidents?.filter(i => i.state === 'SUSPECTED').length || 0;

  const totalNodes = nodes?.length || 0;
  const onlineNodes = nodes?.filter(n => n.state === 'ONLINE').length || 0;
  const degradedNodes = nodes?.filter(n => n.state === 'DEGRADED').length || 0;
  const unreachableNodes = nodes?.filter(n => n.state === 'UNREACHABLE' || n.state === 'OFFLINE').length || 0;

  // Determine overall information condition
  const informationCondition = unreachableNodes > 0 ? 'DEGRADED' : degradedNodes > 0 ? 'DEGRADED' : 'GOOD';

  return {
    isLoading,
    error: nodesError,
    metrics: {
      activeIncidents,
      confirmedIncidents,
      watchIncidents,
      suspectedIncidents,
      incidentSummary: `${confirmedIncidents} confirmed · ${watchIncidents} watch · ${suspectedIncidents} suspected`,
      totalNodes,
      onlineNodes,
      degradedNodes,
      unreachableNodes,
      nodesSummary: degradedNodes > 0 || unreachableNodes > 0
        ? `${degradedNodes} degraded · ${unreachableNodes} unreachable`
        : 'All nodes operational',
      informationCondition,
      informationDetail: unreachableNodes > 0
        ? `${unreachableNodes} node(s) unreachable`
        : degradedNodes > 0
          ? `${degradedNodes} node(s) degraded`
          : 'All systems nominal',
    },
  };
}
