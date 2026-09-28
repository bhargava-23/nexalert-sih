import { type ReactNode, useEffect, useRef, useState } from 'react';
import { Link } from 'wouter';
import {
  AlertTriangle, ArrowDownRight, ArrowRight, Check, ChevronDown, ChevronUp,
  CircleHelp, Clock3, Compass, FileWarning, Flame, LocateFixed, Map as MapIcon,
  MapPin, Navigation, PhoneCall, Radio, ShieldCheck, Signal, Siren, SlidersHorizontal,
  WifiOff, X, Zap,
} from 'lucide-react';
import type { DemoMode, EventRecord, Freshness, HazardState, InfoCondition, MapLayer, SafePlace } from '@/lib/nexalert-data';

export function FreshnessBadge({ value }: { value: Freshness }) {
  const meta = {
    LIVE: ['LIVE', 'bg-[#d9efe8] text-[#195d52] border-[#abd8ca]', Radio],
    RECENT: ['RECENT', 'bg-[#e3eef0] text-[#245b66] border-[#bfd9dc]', Clock3],
    STALE: ['STALE', 'bg-[#f8e9c7] text-[#76521a] border-[#e7c47f]', Clock3],
    UNKNOWN: ['UNKNOWN', 'bg-[#ece9df] text-[#5d625f] border-[#d3cec0]', CircleHelp],
  }[value] as [string, string, typeof Radio];
  const Icon = meta[2];
  return <span data-testid={`badge-freshness-${value.toLowerCase()}`} className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono-safe text-[10px] font-medium tracking-[.12em] ${meta[1]}`}><Icon size={12} aria-hidden="true" />{meta[0]}</span>;
}

export function HazardStateChip({ state }: { state: HazardState }) {
  const config = {
    CONFIRMED: ['CONFIRMED', 'bg-[#f6d9d2] text-[#923d34] border-[#e7b1a5]'],
    WATCH: ['WATCH', 'bg-[#f8e9c7] text-[#76521a] border-[#e7c47f]'],
    RESOLVED: ['RESOLVED', 'bg-[#d9efe8] text-[#195d52] border-[#abd8ca]'],
    UNKNOWN: ['UNKNOWN', 'bg-[#ece9df] text-[#5d625f] border-[#d3cec0]'],
  }[state];
  return <span data-testid={`chip-hazard-${state.toLowerCase()}`} className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono-safe text-[10px] tracking-[.12em] ${config[1]}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{config[0]}</span>;
}

export function SeverityBadge({ severity }: { severity: EventRecord['severity'] }) {
  const colors = { CRITICAL: 'text-[#923d34] bg-[#f6d9d2]', HIGH: 'text-[#8a5319] bg-[#f8e9c7]', MODERATE: 'text-[#245b66] bg-[#e3eef0]', LOW: 'text-[#195d52] bg-[#d9efe8]' };
  return <span data-testid={`badge-severity-${severity.toLowerCase()}`} className={`rounded-md px-2 py-1 font-mono-safe text-[10px] font-medium tracking-[.1em] ${colors[severity]}`}>{severity}</span>;
}

export function SafetyBanner({ event }: { event: EventRecord }) {
  const critical = event.severity === 'CRITICAL';
  return <section data-testid="banner-safety" className={`border-b ${critical ? 'border-[#d9a094] bg-[#f5ddd7]' : 'border-[#d8c78e] bg-[#f8edcd]'}`}>
    <div className="mx-auto flex max-w-6xl items-start gap-3 px-4 py-3 sm:px-6">
      <div className={`mt-0.5 rounded-full p-1.5 ${critical ? 'bg-[#923d34] text-[#fff7ee]' : 'bg-[#8a641e] text-[#fff7ee]'}`}><Siren size={16} aria-hidden="true" /></div>
      <div className="min-w-0 flex-1"><p className="font-mono-safe text-[10px] font-medium tracking-[.16em] text-[#70413a]">{critical ? 'IMMEDIATE SAFETY NOTICE' : 'SAFETY NOTICE'}</p><p className="mt-0.5 text-sm font-semibold text-[#3e302d]">{event.action}</p></div>
      <Link href={`/details/${event.id}`} data-testid="link-banner-details" className="hidden shrink-0 items-center gap-1 pt-1 text-xs font-bold text-[#70413a] sm:flex">Details <ArrowRight size={14} /></Link>
    </div>
  </section>;
}

export function ConnectivityBanner({ mode, condition }: { mode: DemoMode; condition: InfoCondition }) {
  if (mode === 'NORMAL' && condition === 'GOOD') return null;
  const offline = mode === 'OFFLINE';
  return <div data-testid="banner-connectivity" className={`${offline ? 'bg-[#e8e4da] text-[#4f5654]' : 'bg-[#f8e9c7] text-[#76521a]'} border-b border-[#d7cfbb]`}>
    <div className="mx-auto flex max-w-6xl items-center gap-2 px-4 py-2 text-xs font-semibold sm:px-6"><WifiOff size={15} aria-hidden="true" /><span>{offline ? 'OFFLINE LOCAL · Saved information only' : 'DEGRADED CONNECTION · Some live sources may be delayed'}</span>{offline ? <Link href="/offline" data-testid="link-connectivity-offline" className="ml-auto underline underline-offset-2">Offline portal</Link> : <span className="ml-auto font-mono-safe text-[10px] tracking-wide">USE CAUTION</span>}</div>
  </div>;
}

export function EmergencyCard({ event, compact = false }: { event: EventRecord; compact?: boolean }) {
  return <article data-testid={`card-emergency-${event.id}`} className={`overflow-hidden rounded-2xl border border-[#d9a094] bg-[#fff8f4] shadow-[0_12px_32px_rgba(105,53,44,.08)] ${compact ? '' : ''}`}>
    <div className="flex items-center justify-between gap-3 border-b border-[#eed0c7] px-4 py-3 sm:px-5"><div className="flex items-center gap-2"><Flame className="text-[#a8473e]" size={18} aria-hidden="true" /><span className="font-mono-safe text-[10px] font-medium tracking-[.15em] text-[#70413a]">{event.kind}</span></div><div className="flex items-center gap-2"><SeverityBadge severity={event.severity} /><HazardStateChip state={event.state} /></div></div>
    <div className="p-4 sm:p-5">
      <h2 className="font-display text-[clamp(1.55rem,4vw,2.25rem)] font-semibold leading-[1.05] text-[#302a29]">{event.title}</h2>
      <p data-testid="text-event-summary" className="mt-3 max-w-2xl text-sm leading-6 text-[#514a46]">{event.summary}</p>
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-semibold text-[#5a514b]"><span className="inline-flex items-center gap-1.5"><MapPin size={14} className="text-[#a8473e]" />{event.distance} {event.direction}</span><FreshnessBadge value={event.freshness} /></div>
      {!compact && <div className="mt-5 rounded-xl border border-[#e7b1a5] bg-[#f8e7e2] p-3.5"><p className="font-mono-safe text-[10px] tracking-[.14em] text-[#70413a]">RECOMMENDED ACTION</p><p className="mt-1 text-sm font-bold leading-5 text-[#422e2a]">{event.action}</p></div>}
    </div>
  </article>;
}

export function PrimarySafetyAction({ event }: { event: EventRecord }) {
  return <div data-testid="panel-primary-action" className="rounded-2xl border border-[#1a5b5a] bg-[#195d52] p-4 text-[#fff8f4] shadow-[0_12px_28px_rgba(25,93,82,.18)] sm:p-5">
    <div className="flex items-start gap-3"><div className="rounded-lg bg-[#eab34b] p-2 text-[#302a29]"><ArrowDownRight size={20} aria-hidden="true" /></div><div><p className="font-mono-safe text-[10px] tracking-[.16em] text-[#b9ded0]">DO THIS FIRST</p><p className="mt-1 text-lg font-extrabold leading-tight">{event.action}</p></div></div>
    <div className="mt-4 grid grid-cols-2 gap-2 border-t border-[#4b8279] pt-3 text-xs"><span><span className="block font-mono-safe text-[10px] text-[#b9ded0]">DIRECTION</span><strong className="mt-0.5 block">{event.direction}</strong></span><span><span className="block font-mono-safe text-[10px] text-[#b9ded0]">DISTANCE</span><strong className="mt-0.5 block">{event.distance}</strong></span></div>
  </div>;
}

export function LiveMap({ event, mode, layers = ['CURRENT', 'WARNING', 'PROJECTION', 'OPERATIONAL BUFFER'], onToggle }: { event: EventRecord; mode: DemoMode; layers?: MapLayer[]; onToggle?: (layer: MapLayer) => void }) {
  const [expanded, setExpanded] = useState(false);
  const offline = mode === 'OFFLINE';
  return <div data-testid="map-live" className="relative min-h-[280px] overflow-hidden rounded-2xl border border-[#b9c8c5] bg-[#dbe5dc] shadow-[0_10px_28px_rgba(38,61,59,.10)] sm:min-h-[360px]">
    <div className="absolute inset-0 opacity-75" style={{ backgroundImage: 'linear-gradient(28deg, transparent 47%, rgba(255,248,238,.9) 48%, rgba(255,248,238,.9) 50%, transparent 51%), linear-gradient(110deg, transparent 44%, rgba(255,248,238,.9) 45%, rgba(255,248,238,.9) 46%, transparent 47%), repeating-linear-gradient(12deg, rgba(70,110,96,.10) 0 1px, transparent 1px 24px)' }} />
    <div className="absolute -left-12 top-20 h-40 w-[120%] rotate-[-14deg] border-y-[18px] border-[#eab34b]/70 bg-[#d1b96e]/30" />
    <div className="absolute left-[39%] top-[28%] h-36 w-36 rounded-full border-[18px] border-[#c6634e]/45" />
    <div className="absolute left-[41%] top-[31%] h-7 w-7 rounded-full border-4 border-[#fff8f4] bg-[#a8473e] shadow-lg shadow-[#923d34]/40" aria-label="Fire perimeter location" />
    <div className="absolute right-[20%] bottom-[22%] flex h-9 w-9 items-center justify-center rounded-full border-4 border-[#fff8f4] bg-[#195d52] text-[#fff8f4] shadow-lg"><LocateFixed size={16} /></div>
    <div className="absolute left-[calc(41%+1.7rem)] top-[31%] ml-2 mt-1 rounded bg-[#fff8f4]/95 px-2 py-1 font-mono-safe text-[9px] font-medium tracking-wide text-[#70413a]">FIRE · CONFIRMED</div>
    <div className="absolute left-3 top-3 max-w-[calc(100%-1.5rem)] rounded-xl border border-[#c1d1cb] bg-[#fff8f4]/95 p-2.5 backdrop-blur-sm"><p className="font-mono-safe text-[10px] tracking-[.14em] text-[#245b66]">{offline ? 'SAVED MAP · UNKNOWN' : 'CITIZEN MAP · NORTH UP'}</p><p className="mt-1 text-xs font-semibold text-[#3e4b47]">{event.area}</p></div>
    <div className="absolute right-3 top-3 flex flex-col gap-1.5"><button type="button" onClick={() => setExpanded(!expanded)} data-testid="button-map-layers" className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#b9c8c5] bg-[#fff8f4]/95 text-[#245b66] shadow-sm" aria-label="Toggle map layer controls">{expanded ? <X size={18} /> : <SlidersHorizontal size={18} />}</button><button type="button" data-testid="button-map-center" className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#b9c8c5] bg-[#fff8f4]/95 text-[#245b66] shadow-sm" aria-label="Center map on my location"><LocateFixed size={18} /></button></div>
    {expanded && <div className="absolute right-3 top-[5.5rem] z-10 w-52 rounded-xl border border-[#b9c8c5] bg-[#fff8f4]/95 p-3 shadow-lg backdrop-blur-sm"><p className="font-mono-safe text-[10px] tracking-[.13em] text-[#5a6763]">MAP LAYERS</p>{(['CURRENT', 'WARNING', 'PROJECTION', 'OPERATIONAL BUFFER'] as MapLayer[]).map(layer => <label key={layer} className="mt-2 flex cursor-pointer items-center gap-2 text-xs font-semibold text-[#3e4b47]"><input type="checkbox" checked={layers.includes(layer)} onChange={() => onToggle?.(layer)} className="h-4 w-4 accent-[#195d52]" />{layer}</label>)}</div>}
    <div className="absolute bottom-3 left-3 rounded-lg bg-[#fff8f4]/90 px-2.5 py-2 font-mono-safe text-[9px] text-[#5a6763] backdrop-blur-sm"><span className="mr-3">SCALE 2 km</span><span>{offline ? 'NO LIVE TILES' : 'BASEMAP CACHED'}</span></div>
  </div>;
}

export function MapLegend({ layers = ['CURRENT', 'WARNING', 'PROJECTION', 'OPERATIONAL BUFFER'] }: { layers?: MapLayer[] }) {
  const items = { CURRENT: ['#195d52', 'Current position / confirmed'], WARNING: ['#a8473e', 'Confirmed hazard'], PROJECTION: ['#c6634e', 'Forecast movement'], 'OPERATIONAL BUFFER': ['#eab34b', 'Response area / access'] };
  return <div data-testid="map-legend" className="flex flex-wrap gap-x-5 gap-y-2 rounded-xl border border-[#d9d3c6] bg-[#fff8f4] p-3 text-[11px] text-[#4e5b57]">{layers.map(layer => <span key={layer} className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: items[layer][0] }} /> <b className="font-mono-safe text-[9px] tracking-wide">{layer}</b><span className="hidden sm:inline">{items[layer][1]}</span></span>)}</div>;
}

export function SafePlaceCard({ place, onAction }: { place: SafePlace; onAction?: (place: SafePlace) => void }) {
  return <article data-testid={`card-safe-place-${place.id}`} className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4 shadow-[0_8px_22px_rgba(30,48,57,.05)]"><div className="flex items-start justify-between gap-3"><div><p className="font-mono-safe text-[10px] tracking-[.14em] text-[#5a6763]">{place.type}</p><h3 className="mt-1 font-display text-lg font-semibold text-[#302a29]">{place.name}</h3></div><span className={`rounded-full px-2 py-1 font-mono-safe text-[9px] tracking-wide ${place.status === 'OPEN' ? 'bg-[#d9efe8] text-[#195d52]' : place.status === 'LIMITED' ? 'bg-[#f8e9c7] text-[#76521a]' : 'bg-[#ece9df] text-[#5d625f]'}`}>{place.status}</span></div><div className="mt-4 grid grid-cols-2 gap-2 text-xs text-[#59615e]"><span><span className="block font-mono-safe text-[10px] text-[#8a918d]">DISTANCE</span><b className="mt-0.5 block text-[#3e4b47]">{place.distance} · {place.direction}</b></span><span><span className="block font-mono-safe text-[10px] text-[#8a918d]">CAPACITY</span><b className="mt-0.5 block text-[#3e4b47]">{place.capacity}</b></span></div><p className="mt-3 border-t border-[#e8e2d8] pt-3 text-xs leading-5 text-[#6b625d]">{place.caveat}</p><button type="button" onClick={() => onAction?.(place)} data-testid={`button-place-action-${place.id}`} className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[#1f6860] text-sm font-bold text-[#195d52] transition hover:bg-[#e3f1ec]">{place.action}<ArrowRight size={15} /></button></article>;
}

export function SOSControl() {
  const [holding, setHolding] = useState(false);
  const [seconds, setSeconds] = useState(3);
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [sosId, setSOSId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  const sendToBackend = async () => {
    setSending(true);
    setError(null);
    try {
      // Get location if available
      let location: { location_lat?: number; location_lon?: number } = {};
      if ('geolocation' in navigator) {
        try {
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 });
          });
          location.location_lat = position.coords.latitude;
          location.location_lon = position.coords.longitude;
        } catch (err) {
          console.log('[SOS] Location unavailable, sending without location');
        }
      }

      // Send SOS to backend
      const { sendSOSRequest } = await import('@/lib/sos-api');
      const response = await sendSOSRequest({
        ...location,
        device_info: navigator.userAgent,
        message: 'Emergency SOS request from Citizen UI'
      });

      setSOSId(response.sos_id);
      console.log('[SOS] Request sent successfully:', response.sos_id);
    } catch (err: any) {
      console.error('[SOS] Failed to send request:', err);
      setError(err.message || 'Failed to send SOS');
    } finally {
      setSending(false);
    }
  };

  const start = () => {
    if (sent || sending) return;
    setHolding(true);
    setSeconds(3);
    timerRef.current = window.setInterval(() => setSeconds(value => {
      if (value <= 1) {
        window.clearInterval(timerRef.current!);
        setHolding(false);
        setSent(true);
        sendToBackend();
        return 0;
      }
      return value - 1;
    }), 1000);
  };

  const stop = () => { if (!sent && !sending && timerRef.current) { window.clearInterval(timerRef.current); setHolding(false); setSeconds(3); } };
  useEffect(() => () => { if (timerRef.current) window.clearInterval(timerRef.current); }, []);

  return <section data-testid="control-sos" className="rounded-2xl border border-[#a8473e] bg-[#fff8f4] p-4 shadow-[0_10px_26px_rgba(105,53,44,.08)] sm:p-5"><div className="flex items-start gap-3"><div className="rounded-full bg-[#f6d9d2] p-2.5 text-[#923d34]"><PhoneCall size={21} /></div><div><h2 className="font-display text-xl font-semibold text-[#302a29]">Need immediate help?</h2><p className="mt-1 text-sm leading-5 text-[#645955]">Press and hold to send an SOS. This works independently of hazard detection.</p></div></div><button type="button" onPointerDown={start} onPointerUp={stop} onPointerLeave={stop} onKeyDown={event => { if (event.key === ' ' || event.key === 'Enter') start(); }} onKeyUp={event => { if (event.key === ' ' || event.key === 'Enter') stop(); }} data-testid="button-sos-hold" disabled={sending} className={`mt-5 flex min-h-14 w-full items-center justify-center gap-3 rounded-xl font-mono-safe text-sm font-medium tracking-[.08em] text-[#fff8f4] transition ${sosId ? 'bg-[#195d52]' : sending ? 'bg-[#70413a]' : holding ? 'bg-[#70413a]' : 'bg-[#923d34] hover:bg-[#7e362f]'} disabled:opacity-75`} aria-label="Press and hold to send SOS">{sosId ? <><Check size={18} /> SOS SENT · {sosId.substring(0, 8)}</> : sending ? <><Signal size={18} className="animate-pulse" /> SENDING SOS...</> : sent ? <><Signal size={18} /> SENDING...</> : holding ? <><span className="text-xl">{seconds}</span> RELEASE TO CANCEL</> : <><Siren size={18} /> PRESS AND HOLD FOR SOS</>}</button>{sosId && <p className="mt-3 flex items-center gap-2 text-sm font-semibold text-[#195d52]"><Check size={15} /> SOS request delivered to emergency responders</p>}{error && <p className="mt-3 flex items-center gap-2 text-sm font-semibold text-[#923d34]"><AlertTriangle size={15} /> {error}</p>}<p className="mt-3 text-center font-mono-safe text-[9px] tracking-wide text-[#8a817b]">Emergency request is sent immediately after hold completes</p></section>;
}

export function AlertCard({ alert }: { alert: { id: string; title: string; status: string; severity: string; timestamp: string; detail: string } }) {
  const [open, setOpen] = useState(false);
  return <article data-testid={`card-alert-${alert.id}`} className="border-b border-[#e4ddd2] py-4 first:pt-0 last:border-0"><button type="button" onClick={() => setOpen(!open)} data-testid={`button-expand-alert-${alert.id}`} className="flex min-h-11 w-full items-start justify-between gap-4 text-left"><span className="flex items-start gap-3"><span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${alert.status === 'ACTIVE' ? 'bg-[#a8473e]' : 'bg-[#568477]'}`} /><span><span className="flex flex-wrap items-center gap-2"><strong className="font-display text-lg text-[#302a29]">{alert.title}</strong><span className="font-mono-safe text-[9px] tracking-wide text-[#7b817d]">{alert.status}</span></span><span className="mt-1 block text-xs text-[#7b817d]">{alert.timestamp} · {alert.severity}</span></span></span>{open ? <ChevronUp size={18} className="mt-1 text-[#71807a]" /> : <ChevronDown size={18} className="mt-1 text-[#71807a]" />}</button>{open && <p className="ml-5 mt-1 max-w-xl border-l-2 border-[#eab34b] pl-3 text-sm leading-6 text-[#5f625f]">{alert.detail}</p>}</article>;
}

export function ResolutionBanner({ children }: { children: ReactNode }) {
  return <div data-testid="banner-resolution" className="flex items-start gap-3 rounded-xl border border-[#b7d5ca] bg-[#e3f1ec] p-3 text-sm text-[#195d52]"><ShieldCheck size={18} className="mt-0.5 shrink-0" /><span>{children}</span></div>;
}

export function OfflineBanner() {
  return <div data-testid="banner-offline" className="rounded-2xl border border-[#c8c5ba] bg-[#eeeae1] p-4"><div className="flex items-center gap-2 font-mono-safe text-[10px] font-medium tracking-[.16em] text-[#5d625f]"><WifiOff size={15} /> OFFLINE LOCAL PORTAL</div><p className="mt-2 text-sm leading-6 text-[#4d5552]">Live services are unavailable. This screen uses safety information saved on your device and clearly marks what cannot be confirmed.</p></div>;
}

export function EvidenceSummary({ event }: { event: EventRecord }) {
  const [open, setOpen] = useState(false);
  return <section data-testid="panel-evidence" className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><button type="button" onClick={() => setOpen(!open)} data-testid="button-toggle-evidence" className="flex min-h-11 w-full items-center justify-between text-left"><span className="flex items-center gap-2 font-semibold text-[#3e4b47]"><FileWarning size={17} /> Why we are showing this</span>{open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</button>{open && <div className="mt-2 border-t border-[#e4ddd2] pt-3"><p className="text-sm leading-6 text-[#5f625f]">{event.operationalNote}</p><ul className="mt-3 space-y-2">{event.evidence.map((item, index) => <li key={item} className="flex gap-2 text-xs leading-5 text-[#6b716e]"><span className="font-mono-safe text-[#a07a2d]">0{index + 1}</span>{item}</li>)}</ul><p className="mt-3 font-mono-safe text-[10px] tracking-wide text-[#7b817d]">SOURCE · {event.source}</p></div>}</section>;
}

export function DemoControl({ mode, onChange }: { mode: DemoMode; onChange: (mode: DemoMode) => void }) {
  return <label data-testid="control-demo-state" className="flex items-center gap-2 rounded-lg border border-[#50615d] bg-[#263b3a] px-2.5 py-1.5 text-[10px] text-[#dce8dd]"><Zap size={13} className="text-[#eab34b]" /><span className="hidden font-mono-safe tracking-wide sm:inline">DEMO</span><select value={mode} onChange={e => onChange(e.target.value as DemoMode)} data-testid="select-demo-state" className="bg-transparent font-mono-safe text-[10px] font-medium tracking-wide text-[#fff8f4] outline-none"><option className="text-[#302a29]" value="EMERGENCY">EMERGENCY</option><option className="text-[#302a29]" value="NORMAL">NORMAL</option><option className="text-[#302a29]" value="DEGRADED">DEGRADED</option><option className="text-[#302a29]" value="OFFLINE">OFFLINE LOCAL</option></select></label>;
}

export const navItems = [
  { href: '/', label: 'Home', icon: Compass },
  { href: '/map', label: 'Map', icon: MapIcon },
  { href: '/safe-places', label: 'Safe places', icon: Navigation },
  { href: '/alerts', label: 'Alerts', icon: AlertTriangle },
];