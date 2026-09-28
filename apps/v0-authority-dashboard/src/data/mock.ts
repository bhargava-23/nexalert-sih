export type State = 'NORMAL' | 'WATCH' | 'SUSPECTED' | 'CONFIRMED' | 'CRITICAL' | 'RESOLVED';
export type InformationCondition = 'GOOD' | 'DEGRADED' | 'UNKNOWN';
export type NodeState = 'ONLINE' | 'DEGRADED' | 'UNREACHABLE' | 'OFFLINE';

export interface Node {
  id: string;
  name: string;
  kind: 'Weather' | 'Camera' | 'Relay' | 'Seismic' | 'River gauge';
  location: string;
  coordinates: [number, number];
  state: NodeState;
  lastSeen: string;
  battery: number;
  signal: string;
}

export interface Incident {
  id: string;
  title: string;
  hazard: 'Wildfire' | 'Flooding' | 'Seismic' | 'Extreme heat' | 'Infrastructure';
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

export interface HazardGeometry {
  id: string;
  name: string;
  type: 'Current' | 'Warning' | 'Projection' | 'Operational buffer' | 'Impact';
  description: string;
  visible: boolean;
  color: string;
}

export interface MapLayer {
  id: string;
  name: string;
  description: string;
  visible: boolean;
  icon: 'map' | 'nodes' | 'risk' | 'sos' | 'terrain';
}

export interface TelemetryRecord {
  id: string;
  source: string;
  signal: string;
  observed: string;
  state: string;
  receivedAt: string;
  quality: InformationCondition;
}

export interface SOSRequest {
  id: string;
  caller: string;
  location: string;
  receivedAt: string;
  state: 'NEW' | 'TRIAGED' | 'ASSIGNED' | 'RESOLVED';
  note: string;
  channel: 'Mobile' | 'Voice' | 'SMS';
}

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

export interface ResponseAction {
  id: string;
  title: string;
  owner: string;
  state: 'PROPOSED' | 'AUTHORIZED' | 'IN PROGRESS' | 'COMPLETE' | 'BLOCKED';
  due: string;
  note: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  scope: string;
  result: 'Recorded' | 'Rejected' | 'Deferred';
}

export interface SystemService {
  id: string;
  name: string;
  state: 'OPERATIONAL' | 'DEGRADED' | 'UNAVAILABLE';
  detail: string;
  lastCheck: string;
  dependency: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  updated: string;
  mode: 'LIVE' | 'SIMULATION';
}

export const mockNodes: Node[] = [
  { id: 'node-17', name: 'Ridge weather 17', kind: 'Weather', location: 'North ridge', coordinates: [32, 28], state: 'ONLINE', lastSeen: '12 sec ago', battery: 88, signal: '-71 dBm' },
  { id: 'node-04', name: 'Oak relay 04', kind: 'Relay', location: 'Oak valley', coordinates: [54, 52], state: 'ONLINE', lastSeen: '19 sec ago', battery: 74, signal: '-68 dBm' },
  { id: 'node-11', name: 'East cam 11', kind: 'Camera', location: 'East approach', coordinates: [73, 31], state: 'DEGRADED', lastSeen: '4 min ago', battery: 32, signal: '-93 dBm' },
  { id: 'node-29', name: 'Creek gauge 29', kind: 'River gauge', location: 'Black Creek', coordinates: [25, 71], state: 'ONLINE', lastSeen: '36 sec ago', battery: 91, signal: '-62 dBm' },
  { id: 'node-08', name: 'South seismic 08', kind: 'Seismic', location: 'South utility', coordinates: [67, 74], state: 'UNREACHABLE', lastSeen: '42 min ago', battery: 18, signal: '—' },
];

export const mockIncidents: Incident[] = [
  { id: 'INC-24-071', title: 'Juniper Ridge fire', hazard: 'Wildfire', state: 'CONFIRMED', severity: 'Major', informationCondition: 'DEGRADED', freshness: '2 min old', location: 'Juniper Ridge / Sector 4', updatedAt: '08:42:16 UTC', footprint: '1.8 km² current perimeter', evidence: ['Thermal cluster from Ridge weather 17', 'Two camera frames received 08:40 UTC', 'Wind 24 km/h, east-northeast'], recommendation: 'Review west evacuation boundary and stage water tenders north of Route 8.', humanAction: 'No dispatch issued. Authority review required.', },
  { id: 'INC-24-069', title: 'Black Creek rise', hazard: 'Flooding', state: 'WATCH', severity: 'Elevated', informationCondition: 'GOOD', freshness: '41 sec old', location: 'Black Creek / Lowlands', updatedAt: '08:40:51 UTC', footprint: 'Low-lying roads at possible impact', evidence: ['Gauge 29 rising 11 cm / 30 min', 'Rainfall cell upstream', 'No road closure confirmation'], recommendation: 'Maintain watch and request road-closure status from county liaison.', humanAction: 'Monitoring only; no closure authorized.', },
  { id: 'INC-24-064', title: 'South utility vibration', hazard: 'Seismic', state: 'SUSPECTED', severity: 'Advisory', informationCondition: 'UNKNOWN', freshness: '42 min old', location: 'South utility corridor', updatedAt: '08:00:06 UTC', footprint: 'Unknown', evidence: ['One node reported anomalous vibration', 'Node 08 unreachable since report', 'No corroborating public reports'], recommendation: 'Attempt local verification before any public message.', humanAction: 'Awaiting operator verification.', },
  { id: 'INC-24-058', title: 'North heat threshold', hazard: 'Extreme heat', state: 'RESOLVED', severity: 'Advisory', informationCondition: 'GOOD', freshness: '1 hr old', location: 'North basin', updatedAt: '07:35:19 UTC', footprint: 'Resolved', evidence: ['Cooling trend confirmed', 'Shelter capacity returned to normal'], recommendation: 'Close monitoring record.', humanAction: 'Resolved by duty officer.', },
];

export const mockHazards: HazardGeometry[] = [
  { id: 'current', name: 'Current perimeter', type: 'Current', description: 'Observed perimeter; not a forecast', visible: true, color: '#ef765f' },
  { id: 'warning', name: 'Warning zone', type: 'Warning', description: 'Operator-defined review boundary', visible: true, color: '#f4ba5a' },
  { id: 'projection', name: 'Projection envelope', type: 'Projection', description: 'Model geometry; requires human review', visible: true, color: '#e0ca64' },
  { id: 'buffer', name: 'Operational buffer', type: 'Operational buffer', description: 'Planning buffer around geometry', visible: true, color: '#91b277' },
];

export const mockLayers: MapLayer[] = [
  { id: 'incidents', name: 'Incident markers', description: 'Active and observed incident locations', visible: true, icon: 'map' },
  { id: 'nodes', name: 'Field nodes', description: 'Distributed sensing and relay nodes', visible: true, icon: 'nodes' },
  { id: 'links', name: 'Logical links', description: 'Dotted local network relationships', visible: true, icon: 'terrain' },
  { id: 'risk', name: 'Risk overlay', description: 'Qualitative planning context only', visible: true, icon: 'risk' },
  { id: 'sos', name: 'Citizen SOS', description: 'Incoming requests requiring triage', visible: true, icon: 'sos' },
];

export const mockTelemetry: TelemetryRecord[] = [
  { id: 'tel-001', source: 'Ridge weather 17', signal: 'thermal_index', observed: '82.4 °C', state: 'Elevated', receivedAt: '08:42:14 UTC', quality: 'GOOD' },
  { id: 'tel-002', source: 'Ridge weather 17', signal: 'wind_vector', observed: 'ENE / 24 km/h', state: 'Observed', receivedAt: '08:42:12 UTC', quality: 'GOOD' },
  { id: 'tel-003', source: 'East cam 11', signal: 'frame_match', observed: 'Smoke / low visibility', state: 'Suspected', receivedAt: '08:38:01 UTC', quality: 'DEGRADED' },
  { id: 'tel-004', source: 'South seismic 08', signal: 'vibration_rms', observed: '0.68 g', state: 'Anomalous', receivedAt: '08:00:06 UTC', quality: 'UNKNOWN' },
];

export const mockSOS: SOSRequest[] = [
  { id: 'SOS-8841', caller: 'A. Navarro', location: 'Route 8, mile 14', receivedAt: '08:41:37 UTC', state: 'NEW', note: 'Smoke crossing roadway; two people stopped.', channel: 'Mobile' },
  { id: 'SOS-8837', caller: 'Unlisted caller', location: 'Oak valley cabins', receivedAt: '08:35:02 UTC', state: 'TRIAGED', note: 'Needs mobility assistance. Callback requested.', channel: 'Voice' },
  { id: 'SOS-8826', caller: 'M. Chen', location: 'Black Creek footbridge', receivedAt: '08:22:44 UTC', state: 'ASSIGNED', note: 'Water rising near footbridge; moved to high ground.', channel: 'SMS' },
  { id: 'SOS-8812', caller: 'J. Patel', location: 'North basin shelter', receivedAt: '07:56:11 UTC', state: 'RESOLVED', note: 'Transport request completed.', channel: 'Mobile' },
];

export const mockAlerts: AlertLifecycle[] = [
  { id: 'ALT-1904', title: 'Juniper Ridge: route advisory', audience: 'Route 8 travelers', state: 'REVIEW', channel: 'Web / SMS draft', owner: 'Duty officer K. Lin', lastChange: '08:39 UTC' },
  { id: 'ALT-1901', title: 'Black Creek monitoring notice', audience: 'Lowlands residents', state: 'AUTHORIZED', channel: 'Web / siren', owner: 'Ops lead M. Santos', lastChange: '08:31 UTC' },
  { id: 'ALT-1897', title: 'North basin heat notice', audience: 'North basin residents', state: 'EXPIRED', channel: 'Web / SMS', issuedAt: '06:11 UTC', owner: 'Duty officer K. Lin', lastChange: '07:35 UTC' },
];

export const mockActions: ResponseAction[] = [
  { id: 'ACT-442', title: 'Review west evacuation boundary', owner: 'Duty officer K. Lin', state: 'PROPOSED', due: '08:55 UTC', note: 'Recommendation from INC-24-071. No dispatch implied.' },
  { id: 'ACT-438', title: 'Confirm Route 8 closure status', owner: 'County liaison', state: 'IN PROGRESS', due: '08:48 UTC', note: 'Manual confirmation requested.' },
  { id: 'ACT-430', title: 'Stage water tenders north of Route 8', owner: 'Fire liaison', state: 'AUTHORIZED', due: '09:10 UTC', note: 'Authorized by incident commander at 08:21 UTC.' },
  { id: 'ACT-421', title: 'Verify South utility vibration', owner: 'Field verification', state: 'BLOCKED', due: '09:30 UTC', note: 'Node 08 unreachable; local verification required.' },
];

export const mockAudit: AuditEvent[] = [
  { id: 'AUD-9918', timestamp: '08:42:16 UTC', actor: 'System / ingest', action: 'Updated incident evidence', scope: 'INC-24-071', result: 'Recorded' },
  { id: 'AUD-9917', timestamp: '08:41:55 UTC', actor: 'K. Lin', action: 'Opened action review', scope: 'ACT-442', result: 'Recorded' },
  { id: 'AUD-9916', timestamp: '08:41:37 UTC', actor: 'Citizen gateway', action: 'Received SOS request', scope: 'SOS-8841', result: 'Recorded' },
  { id: 'AUD-9915', timestamp: '08:39:11 UTC', actor: 'M. Santos', action: 'Changed alert lifecycle', scope: 'ALT-1901', result: 'Recorded' },
  { id: 'AUD-9914', timestamp: '08:38:50 UTC', actor: 'K. Lin', action: 'Attempted public issue', scope: 'ALT-1904', result: 'Deferred' },
];

export const mockServices: SystemService[] = [
  { id: 'svc-1', name: 'Master coordination service', state: 'OPERATIONAL', detail: 'Local authority master available', lastCheck: '12 sec ago', dependency: 'Local network' },
  { id: 'svc-2', name: 'Node ingest gateway', state: 'DEGRADED', detail: 'East camera path delayed', lastCheck: '34 sec ago', dependency: 'Field relay mesh' },
  { id: 'svc-3', name: 'Citizen gateway', state: 'OPERATIONAL', detail: 'Inbound queue accepting requests', lastCheck: '8 sec ago', dependency: 'Internet / cellular' },
  { id: 'svc-4', name: 'Internet uplink', state: 'UNAVAILABLE', detail: 'Internet unavailable; local mode active', lastCheck: '18 min ago', dependency: 'County WAN' },
];

export const mockScenarios: Scenario[] = [
  { id: 'scenario-live', name: 'Current operational picture', description: 'Read-only live geometry and telemetry context', updated: '08:42 UTC', mode: 'LIVE' },
  { id: 'scenario-wind', name: 'ENE wind shift / 30 min', description: 'Simulation only; does not alter live incident state', updated: 'Yesterday 14:12 UTC', mode: 'SIMULATION' },
  { id: 'scenario-rain', name: 'Upstream rainfall pulse', description: 'Simulation only; compare lowlands impact envelope', updated: 'Yesterday 09:08 UTC', mode: 'SIMULATION' },
];

export const navGroups = [
  { label: 'Command', items: [{ href: '/overview', label: 'Live command picture', icon: 'Command' }, { href: '/incidents', label: 'Incidents', icon: 'Incidents' }, { href: '/fire-spread', label: 'Fire spread', icon: 'Flame' }, { href: '/affected-area', label: 'Affected area', icon: 'Area' }, { href: '/multi-hazard', label: 'Multi-hazard', icon: 'Layers' }] },
  { label: 'Field intelligence', items: [{ href: '/nodes', label: 'Nodes', icon: 'Nodes' }, { href: '/telemetry', label: 'Telemetry', icon: 'Activity' }, { href: '/citizen-sos', label: 'Citizen SOS', icon: 'Sos' }] },
  { label: 'Coordination', items: [{ href: '/alerts', label: 'Alerts', icon: 'Bell' }, { href: '/historical', label: 'Historical', icon: 'History' }, { href: '/response', label: 'Response', icon: 'Response' }, { href: '/audit', label: 'Audit trail', icon: 'Audit' }, { href: '/system', label: 'System', icon: 'System' }] },
] as const;