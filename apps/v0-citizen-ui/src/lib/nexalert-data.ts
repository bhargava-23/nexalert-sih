export type Freshness = 'LIVE' | 'RECENT' | 'STALE' | 'UNKNOWN';
export type InfoCondition = 'GOOD' | 'DEGRADED' | 'UNKNOWN';
export type HazardState = 'CONFIRMED' | 'WATCH' | 'RESOLVED' | 'UNKNOWN';
export type MapLayer = 'CURRENT' | 'WARNING' | 'PROJECTION' | 'OPERATIONAL BUFFER';

export interface EventRecord {
  id: string;
  title: string;
  kind: string;
  state: HazardState;
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  summary: string;
  action: string;
  distance: string;
  direction: string;
  area: string;
  updatedAt: string;
  freshness: Freshness;
  source: string;
  evidence: string[];
  operationalNote: string;
}

export interface SafePlace {
  id: string;
  name: string;
  type: 'SHELTER' | 'OPEN SAFE AREA' | 'HOSPITAL';
  distance: string;
  direction: string;
  status: 'OPEN' | 'LIMITED' | 'UNKNOWN';
  capacity: string;
  caveat: string;
  action: string;
}

export interface AlertRecord {
  id: string;
  title: string;
  status: 'ACTIVE' | 'RESOLVED';
  severity: 'CRITICAL' | 'HIGH' | 'MODERATE';
  timestamp: string;
  detail: string;
}

// Mock data for initial UI - will be replaced with real backend data
export const event: EventRecord = {
  id: 'no-event',
  title: 'No active emergency',
  kind: 'COMMUNITY STATUS',
  state: 'WATCH',
  severity: 'LOW',
  summary: 'No confirmed emergency is currently within your area.',
  action: 'Keep notifications enabled and review your nearest safe place.',
  distance: '—',
  direction: 'local area',
  area: 'Your area',
  updatedAt: 'Checked recently',
  freshness: 'LIVE',
  source: 'NexAlert regional feed',
  evidence: ['No active regional alert matches your location.'],
  operationalNote: 'Conditions can change. NexAlert will notify you when an alert is confirmed.',
};

export const safePlaces: SafePlace[] = [];

export const alerts: AlertRecord[] = [];