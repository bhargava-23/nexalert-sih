import * as React from 'react';
import { type ReactNode, createContext, useContext, useMemo, useState, useEffect } from 'react';
import { Link, Route, Switch, useLocation, useParams, Router as WouterRouter } from 'wouter';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AlertTriangle, ArrowRight, Bell, Check, ChevronRight, CircleHelp, Globe2, HeartPulse, Home as HomeIcon, Languages, LockKeyhole, Menu, Settings as SettingsIcon, ShieldCheck, SlidersHorizontal, Smartphone, ThermometerSun, Volume2, Wifi, X } from 'lucide-react';
import NotFound from '@/pages/not-found';
import { AlertCard, EmergencyCard, EvidenceSummary, FreshnessBadge, HazardStateChip, MapLegend, PrimarySafetyAction, SafePlaceCard, SOSControl, SafetyBanner, SeverityBadge, navItems } from '@/components/nexalert-components';
import { RealMap } from '@/components/real-map';
import { NotificationSettings } from '@/components/notification-settings';
import { event as defaultEvent, safePlaces, type MapLayer, type SafePlace, type EventRecord } from '@/lib/nexalert-data';
import { getCurrentEmergency } from '@/lib/backend-api';
import { offlineWs } from '@/lib/offline-ws';

const queryClient = new QueryClient();

export type NetworkState = 'NORMAL' | 'DEGRADED' | 'OFFLINE_LOCAL' | 'EMERGENCY' | 'RESOLVED';

interface AppContextValue {
  currentEvent: EventRecord;
  refreshEvent: () => Promise<void>;
  networkState: NetworkState;
}

const AppContext = createContext<AppContextValue | null>(null);
function useNexAlert() {
  const value = useContext(AppContext);
  if (!value) throw new Error('NexAlert context is missing');
  return value;
}

function Shell({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const [menuOpen, setMenuOpen] = React.useState(false);
  return <div className="nx-app-shell nx-grain min-h-[100dvh]">
    <header className="sticky top-0 z-30 border-b border-[#243c3b] bg-[#1e3433] text-[#fff8f4] shadow-[0_4px_18px_rgba(30,52,51,.18)]">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
        <Link href="/" data-testid="link-brand-home" className="flex min-h-11 items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#eab34b] text-[#1e3433]"><ShieldCheck size={21} strokeWidth={2.2} /></span>
          <span><span className="block font-display text-lg font-bold leading-none tracking-tight">NexAlert</span><span className="mt-1 block font-mono-safe text-[8px] tracking-[.18em] text-[#b9d0c7]">CITIZEN SAFETY</span></span>
        </Link>
        <button type="button" onClick={() => setMenuOpen(!menuOpen)} data-testid="button-mobile-menu" className="flex h-11 w-11 items-center justify-center rounded-lg border border-[#50615d] text-[#fff8f4] md:hidden" aria-label="Open navigation">{menuOpen ? <X size={19} /> : <Menu size={19} />}</button>
      </div>
      <nav className="hidden border-t border-[#38504d] md:block" aria-label="Primary navigation"><div className="mx-auto flex max-w-6xl items-center gap-1 px-6">{[...navItems, { href: '/alerts', label: 'Alerts', icon: Bell }].filter((item, index, all) => all.findIndex(other => other.href === item.href) === index).map(item => { const Icon = item.icon; return <Link key={item.href} href={item.href} data-testid={`link-nav-${item.label.toLowerCase().replace(' ', '-')}`} className={`flex min-h-12 items-center gap-2 border-b-2 px-3 text-xs font-semibold transition ${location === item.href ? 'border-[#eab34b] text-[#fff8f4]' : 'border-transparent text-[#b9d0c7] hover:text-[#fff8f4]'}`}><Icon size={15} />{item.label}</Link>; })}<Link href="/sos" data-testid="link-nav-sos" className={`ml-auto flex min-h-12 items-center gap-2 border-b-2 px-3 text-xs font-bold ${location === '/sos' ? 'border-[#eab34b] text-[#eab34b]' : 'border-transparent text-[#f0b5a8]'}`}><HeartPulse size={15} />SOS</Link><Link href="/settings" data-testid="link-nav-settings" className="flex min-h-12 items-center px-3 text-[#b9d0c7] hover:text-[#fff8f4]" aria-label="Settings"><SettingsIcon size={16} /></Link></div></nav>
    </header>
    {menuOpen && <div className="fixed inset-x-0 top-[69px] z-20 border-b border-[#d9d3c6] bg-[#fff8f4] p-3 shadow-lg md:hidden"><div className="grid grid-cols-2 gap-2">{[...navItems, { href: '/alerts', label: 'Alerts', icon: Bell }, { href: '/sos', label: 'SOS', icon: HeartPulse }, { href: '/settings', label: 'Settings', icon: SettingsIcon }].filter((item, index, all) => all.findIndex(other => other.href === item.href) === index).map(item => { const Icon = item.icon; return <Link key={item.href} href={item.href} onClick={() => setMenuOpen(false)} data-testid={`link-mobile-${item.label.toLowerCase().replace(' ', '-')}`} className="flex min-h-12 items-center gap-2 rounded-xl bg-[#f1eee6] px-3 text-sm font-bold text-[#304c4a]"><Icon size={17} />{item.label}</Link>; })}</div></div>}
    <main className="pb-24 md:pb-10">{children}</main>
    <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[#d9d3c6] bg-[#fff8f4]/95 p-2 backdrop-blur-md md:hidden" aria-label="Mobile navigation"><div className="mx-auto grid max-w-lg grid-cols-5 gap-1">{[...navItems.slice(0, 3), { href: '/alerts', label: 'Alerts', icon: Bell }, { href: '/sos', label: 'SOS', icon: HeartPulse }].map(item => { const Icon = item.icon; const active = location === item.href; return <Link key={item.href} href={item.href} data-testid={`link-bottom-${item.label.toLowerCase().replace(' ', '-')}`} className={`flex min-h-11 flex-col items-center justify-center gap-1 rounded-lg text-[10px] font-bold ${active ? 'bg-[#e3f1ec] text-[#195d52]' : 'text-[#71807a]'}`}><Icon size={17} /><span>{item.label}</span></Link>; })}</div></nav>
  </div>;
}

function PageFrame({ eyebrow, title, intro, children }: { eyebrow: string; title: string; intro?: string; children: ReactNode }) {
  return <div className="nx-page-enter mx-auto max-w-6xl px-4 py-7 sm:px-6 sm:py-10"><div className="max-w-3xl"><p className="font-mono-safe text-[10px] font-medium tracking-[.18em] text-[#688078]">{eyebrow}</p><h1 className="mt-2 font-display text-[clamp(2rem,5vw,3.8rem)] font-semibold leading-[.98] tracking-[-.03em] text-[#283a39]">{title}</h1>{intro && <p className="mt-4 max-w-2xl text-sm leading-6 text-[#65706b]">{intro}</p>}</div>{children}</div>;
}

function Home() {
  const { currentEvent } = useNexAlert();
  return <><SafetyBanner event={currentEvent} /><PageFrame eyebrow="YOUR LOCAL STATUS" title="Know what to do next." intro="NexAlert monitors your area. Keep this page available if conditions change."><div className="mt-7 grid gap-5 lg:grid-cols-[1.18fr_.82fr]"><div className="space-y-5"><EmergencyCard event={currentEvent} /><PrimarySafetyAction event={currentEvent} /><div className="grid gap-4 sm:grid-cols-2"><Link href="/map" data-testid="link-home-map" className="group flex min-h-16 items-center justify-between rounded-2xl border border-[#c6d6d0] bg-[#e3f1ec] px-4 text-sm font-bold text-[#195d52] transition hover:border-[#195d52]"><span className="flex items-center gap-2"><SlidersHorizontal size={18} />Open safety map</span><ArrowRight size={17} className="transition group-hover:translate-x-1" /></Link><Link href="/safe-places" data-testid="link-home-safe-places" className="group flex min-h-16 items-center justify-between rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] px-4 text-sm font-bold text-[#304c4a] transition hover:border-[#195d52]"><span className="flex items-center gap-2"><HomeIcon size={18} />Find a safe place</span><ArrowRight size={17} className="transition group-hover:translate-x-1" /></Link></div></div><div className="space-y-5"><RealMap /><MapLegend layers={['CURRENT', 'WARNING', 'PROJECTION']} /><SOSControl /></div></div><div className="mt-6 grid gap-4 md:grid-cols-3"><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-wide text-[#7b817d]">LAST CHECK</p><p className="mt-2 text-sm font-bold text-[#3e4b47]">{currentEvent.updatedAt}</p><FreshnessBadge value={currentEvent.freshness} /></div><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-wide text-[#7b817d]">INFORMATION CONDITION</p><p className="mt-2 text-sm font-bold text-[#3e4b47]">GOOD</p><p className="mt-1 text-xs text-[#74817c]">See freshness on every alert</p></div><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-wide text-[#7b817d]">EMERGENCY ACCESS</p><p className="mt-2 text-sm font-bold text-[#3e4b47]">SOS is always available</p><Link href="/sos" data-testid="link-home-sos" className="mt-1 inline-flex items-center gap-1 text-xs font-bold text-[#923d34]">Review SOS flow <ChevronRight size={14} /></Link></div></div></PageFrame></>;
}

function MapPage() {
  const { currentEvent } = useNexAlert();
  return <PageFrame eyebrow="ORIENTATION, NOT CERTAINTY" title="Safety map" intro="Map shows your location and context. It is not a promise that a road is open or a route is safe. Check local instructions before moving."><div className="mt-7 space-y-4"><RealMap /><MapLegend layers={['CURRENT', 'WARNING', 'PROJECTION', 'OPERATIONAL BUFFER']} /><div className="grid gap-4 md:grid-cols-2"><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-[.15em] text-[#688078]">MAP SEMANTICS</p><div className="mt-3 space-y-3 text-sm text-[#5f625f]"><p><b className="text-[#195d52]">CURRENT</b> · your location and confirmed conditions</p><p><b className="text-[#a8473e]">WARNING</b> · active confirmed hazard area</p><p><b className="text-[#c6634e]">PROJECTION</b> · possible movement, not a boundary</p><p><b className="text-[#a07a2d]">OPERATIONAL BUFFER</b> · response or access context</p></div></div><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><div className="flex items-center gap-2 text-[#304c4a]"><CircleHelp size={17} /><p className="font-semibold">If tiles do not load</p></div><p className="mt-2 text-sm leading-6 text-[#69716e]">Use the text summary below. It stays useful when map services are unavailable.</p><div className="mt-3 rounded-xl bg-[#eeeae1] p-3 text-sm font-semibold leading-5 text-[#4d5552]"><span className="font-mono-safe text-[10px] tracking-wide text-[#7b817d]">TEXT SAFETY FALLBACK</span><br />{currentEvent.title} is {currentEvent.distance} {currentEvent.direction}. {currentEvent.action}</div></div></div></div></PageFrame>;
}

function SafePlacesPage() {
  const { currentEvent } = useNexAlert();
  const [notice, setNotice] = React.useState('');
  const action = (place: SafePlace) => setNotice(`${place.name}: ${place.caveat}`);
  return <PageFrame eyebrow="DESTINATIONS WITH CAVEATS" title="Find a safer place" intro="Ranked by distance and reported operating status. No route is guaranteed safe while an emergency is active."><div className="mt-7 space-y-5">{safePlaces.length === 0 && <div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-6 text-center"><p className="text-sm text-[#5a6763]">No safe places are currently reported in your area.</p></div>}{safePlaces.length > 0 && <><div className="rounded-2xl border border-[#eab34b] bg-[#fff3d6] p-4"><div className="flex items-start gap-3"><ThermometerSun size={19} className="mt-0.5 text-[#8a641e]" /><p className="text-sm leading-6 text-[#5f4b27]"><b>Exposure first.</b> If smoke is visible, stay upwind and avoid outdoor assembly areas. Current threat is {currentEvent.distance} {currentEvent.direction}.</p></div></div>{notice && <div className="rounded-xl border border-[#b7d5ca] bg-[#e3f1ec] p-3 text-sm text-[#195d52]"><ShieldCheck size={18} className="mt-0.5 inline shrink-0 mr-2" /><span>{notice}</span></div>}<div className="grid gap-4 md:grid-cols-3">{safePlaces.map(place => <SafePlaceCard key={place.id} place={place} onAction={action} />)}</div></>}<div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-[.14em] text-[#688078]">SHELTER FALLBACK</p><h2 className="mt-2 font-display text-xl font-semibold text-[#302a29]">No destination is reported open?</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-[#65706b]">Move away from the hazard using a route local responders have confirmed. If you need urgent help, use SOS independently of this list.</p><Link href="/sos" data-testid="link-safe-places-sos" className="mt-4 inline-flex min-h-11 items-center gap-2 rounded-xl bg-[#923d34] px-4 text-sm font-bold text-[#fff8f4]">Open SOS <ArrowRight size={16} /></Link></div></div></PageFrame>;
}

function AlertsPage() {
  return <PageFrame eyebrow="WHAT HAS CHANGED" title="Alerts" intro="Active alerts stay first. Resolved alerts remain visible so you can understand recent changes without mistaking them for current danger."><div className="mt-7 grid gap-5 lg:grid-cols-[1fr_.65fr]"><section className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4 sm:p-5"><div className="mb-4 flex items-center justify-between"><h2 className="font-display text-xl font-semibold text-[#302a29]">Regional alert log</h2><span className="font-mono-safe text-[10px] tracking-wide text-[#7b817d]">{alerts.length} ITEMS</span></div>{alerts.length === 0 ? <p className="py-6 text-center text-sm text-[#5a6763]">No alerts at this time</p> : alerts.map(alert => <AlertCard key={alert.id} alert={alert} />)}</section><div className="space-y-4"><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-[.14em] text-[#688078]">FRESHNESS KEY</p><div className="mt-3 flex flex-wrap gap-2"><FreshnessBadge value="LIVE" /><FreshnessBadge value="RECENT" /><FreshnessBadge value="STALE" /><FreshnessBadge value="UNKNOWN" /></div><p className="mt-3 text-xs leading-5 text-[#69716e]">Freshness is always shown separately from the hazard state. A confirmed event can become stale when the network is delayed.</p></div><div className="rounded-2xl border border-[#d9d3c6] bg-[#eeeae1] p-4"><div className="flex items-center gap-2"><Wifi size={17} className="text-[#195d52]" /><p className="font-semibold text-[#3e4b47]">Information condition</p></div><p className="mt-2 font-mono-safe text-xs tracking-wide text-[#5a6763]">GOOD</p><p className="mt-1 text-xs leading-5 text-[#69716e]">Never infer certainty from a color alone. Read the state and timestamp together.</p></div></div></div></PageFrame>;
}

function SosPage() {
  return <PageFrame eyebrow="INDEPENDENT EMERGENCY CHANNEL" title="SOS" intro="SOS is for immediate personal danger. It does not wait for a hazard alert and it does not require the map to work."><div className="mt-7 grid gap-5 lg:grid-cols-[.85fr_1.15fr]"><SOSControl /><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4 sm:p-5"><p className="font-mono-safe text-[10px] tracking-[.15em] text-[#688078]">BEFORE YOU SEND</p><ol className="mt-4 space-y-4">{['Get to a position with the clearest view or air.', 'Press and hold the SOS control for three seconds.', 'Keep this device available. Delivery status will be shown here.'].map((item, index) => <li key={item} className="flex gap-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#e3f1ec] font-mono-safe text-xs font-bold text-[#195d52]">0{index + 1}</span><p className="text-sm leading-6 text-[#5f625f]">{item}</p></li>)}</ol><div className="mt-5 rounded-xl bg-[#f1eee6] p-3 text-xs leading-5 text-[#69716e]"><b className="text-[#4d5552]">If voice service is available:</b> call your local emergency number directly. NexAlert does not replace emergency dispatch.</div></div></div></PageFrame>;
}

function DetailsPage() {
  const { currentEvent } = useNexAlert();
  const params = useParams<{ eventId: string }>();
  return <PageFrame eyebrow="PROGRESSIVE DETAIL" title={currentEvent.title} intro={`Event ID: ${params.eventId || currentEvent.id}`}><div className="mt-7 grid gap-5 lg:grid-cols-[1fr_.75fr]"><div className="space-y-5"><EmergencyCard event={currentEvent} /><div className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4"><p className="font-mono-safe text-[10px] tracking-[.15em] text-[#688078]">EVENT RECORD</p><dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-4 text-sm"><div><dt className="text-xs text-[#87908b]">Hazard state</dt><dd className="mt-1"><HazardStateChip state={currentEvent.state} /></dd></div><div><dt className="text-xs text-[#87908b]">Severity</dt><dd className="mt-1"><SeverityBadge severity={currentEvent.severity} /></dd></div><div><dt className="text-xs text-[#87908b]">Freshness</dt><dd className="mt-1"><FreshnessBadge value={currentEvent.freshness} /></dd></div><div><dt className="text-xs text-[#87908b]">Area</dt><dd className="mt-1 font-semibold text-[#3e4b47]">{currentEvent.area}</dd></div></dl></div></div><div className="space-y-5"><EvidenceSummary event={currentEvent} /><Link href="/map" data-testid="link-details-map" className="flex min-h-14 items-center justify-between rounded-2xl border border-[#c6d6d0] bg-[#e3f1ec] px-4 text-sm font-bold text-[#195d52]">View this event on the map <ArrowRight size={17} /></Link></div></div></PageFrame>;
}

function SettingsPage() {
  const [saved, setSaved] = React.useState(false);
  return <PageFrame eyebrow="YOUR DEVICE, YOUR SIGNAL" title="Settings" intro="Choose how NexAlert should behave when attention, power, or network access is limited."><div className="mt-7 max-w-2xl space-y-4"><section className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4 sm:p-5"><h2 className="font-display text-xl font-semibold text-[#302a29]">Emergency Notifications</h2><p className="mt-2 text-sm text-[#5a6763]">Receive critical hazard alerts directly on this device, even when the app is closed.</p><div className="mt-4 border-t border-[#eee8dd] pt-4"><NotificationSettings /></div></section><section className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4 sm:p-5"><h2 className="font-display text-xl font-semibold text-[#302a29]">Location and notifications</h2>{[['location', 'Location sharing', 'Used to measure distance and order safe places', LocateIcon], ['language', 'Plain-language mode', 'Use short instructions before technical detail', Languages]].map(([id, label, detail, Icon]) => <label key={id as string} className="mt-4 flex min-h-14 cursor-pointer items-center gap-3 border-t border-[#eee8dd] pt-4"><span className="rounded-lg bg-[#e3f1ec] p-2 text-[#195d52]">{typeof Icon === 'function' && <Icon size={17} />}</span><span className="flex-1"><b className="block text-sm text-[#3e4b47]">{label as string}</b><small className="mt-0.5 block text-xs leading-5 text-[#7b817d]">{detail as string}</small></span><input defaultChecked type="checkbox" data-testid={`input-setting-${id as string}`} className="h-5 w-5 accent-[#195d52]" /></label>)}</section><section className="rounded-2xl border border-[#d9d3c6] bg-[#fff8f4] p-4 sm:p-5"><h2 className="font-display text-xl font-semibold text-[#302a29]">Accessibility and deployment</h2>{[['accessibility', 'Reduce motion', Volume2], ['deployment', 'Network-aware mode', Wifi], ['privacy', 'Private device', LockKeyhole]].map(([id, label, Icon]) => <label key={id as string} className="mt-4 flex min-h-12 items-center gap-3 border-t border-[#eee8dd] pt-4"><span className="text-[#688078]">{typeof Icon === 'function' && <Icon size={17} />}</span><span className="flex-1 text-sm font-semibold text-[#3e4b47]">{label as string}</span><input type="checkbox" data-testid={`input-setting-${id as string}`} className="h-5 w-5 accent-[#195d52]" /></label>)}<button type="button" onClick={() => setSaved(true)} data-testid="button-save-settings" className="mt-5 flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#195d52] text-sm font-bold text-[#fff8f4]">{saved ? <><Check size={17} /> Settings saved locally</> : 'Save settings'}</button></section></div></PageFrame>;
}

function LocateIcon(props: { size?: number }) { return <Globe2 {...props} aria-hidden="true" />; }

function Router() {
  return <ErrorBoundary resetKey={useLocation()[0]}><Switch><Route path="/" component={Home} /><Route path="/map" component={MapPage} /><Route path="/safe-places" component={SafePlacesPage} /><Route path="/alerts" component={AlertsPage} /><Route path="/sos" component={SosPage} /><Route path="/details/:eventId" component={DetailsPage} /><Route path="/settings" component={SettingsPage} /><Route component={NotFound} /></Switch></ErrorBoundary>;
}

function App() {
  const [currentEvent, setCurrentEvent] = useState<EventRecord>(defaultEvent);
  const [networkState, setNetworkState] = useState<NetworkState>('NORMAL');

  // Fetch real backend emergency state on mount and periodically
  useEffect(() => {
    const fetchEmergency = async () => {
      const emergency = await getCurrentEmergency();
      if (emergency) {
        console.log('[App] Active emergency detected:', emergency.title);
        setCurrentEvent(emergency);
      } else {
        console.log('[App] No active emergency');
        setCurrentEvent(defaultEvent);
      }
    };

    // Fetch on mount
    fetchEmergency();

    // Refresh every 30 seconds
    const interval = setInterval(fetchEmergency, 30000);

    return () => clearInterval(interval);
  }, []);

  const refreshEvent = async () => {
    const emergency = await getCurrentEmergency();
    if (emergency) {
      setCurrentEvent(emergency);
    } else {
      setCurrentEvent(defaultEvent);
    }
  };

  const value = useMemo(() => ({ currentEvent, refreshEvent, networkState }), [currentEvent, networkState]);

  return <QueryClientProvider client={queryClient}><TooltipProvider><AppContext.Provider value={value}><WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}><Shell><Router /></Shell></WouterRouter></AppContext.Provider><Toaster /></TooltipProvider></QueryClientProvider>;
}

export default App;
