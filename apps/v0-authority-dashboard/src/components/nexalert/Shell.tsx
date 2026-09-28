import { useState, type ReactNode } from 'react';
import { Link, useLocation } from 'wouter';
import {
  Activity, AreaChart, Bell, Boxes, Cable, CircleHelp, Command, FileClock,
  Flame, History, Layers3, Menu, Radio, Search, Settings2, ShieldAlert, Siren,
  TriangleAlert, X,
  type LucideIcon,
} from 'lucide-react';
import { navGroups } from '@/data/mock';

const icons: Record<string, LucideIcon> = {
  Command, Incidents: ShieldAlert, Flame, Area: AreaChart, Layers: Layers3,
  Nodes: Boxes, Activity, Sos: Siren, Bell, History, Response: Cable,
  Audit: FileClock, System: Settings2,
};

function Mark() {
  return (
    <div className="flex items-center gap-3 px-4 py-4">
      <div className="relative grid h-8 w-8 place-items-center rounded-md border border-cyan-400/50 bg-cyan-400/10 text-cyan-300">
        <ShieldAlert size={18} strokeWidth={1.8} />
        <span className="absolute -bottom-1 -right-1 h-2 w-2 rounded-full bg-amber-300 ring-2 ring-[#0d1521]" />
      </div>
      <div className="sidebar-wordmark">
        <div className="title-display text-[15px] tracking-wide text-slate-100">NexAlert</div>
        <div className="mt-0.5 font-mono text-[9px] uppercase tracking-[.18em] text-slate-500">Authority console</div>
      </div>
    </div>
  );
}

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  const [location] = useLocation();
  return (
    <nav className="app-scrollbar flex-1 overflow-y-auto px-3 pb-3">
      {navGroups.map((group) => (
        <div key={group.label} className="mb-5">
          <div className="sidebar-meta mb-2 px-3 font-mono text-[9px] font-bold uppercase tracking-[.18em] text-slate-600">{group.label}</div>
          <div className="space-y-0.5">
            {group.items.map((item) => {
              const Icon = icons[item.icon] || Command;
              const active = location === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  data-testid={`link-nav-${item.href.slice(1)}`}
                  className={`nav-item group flex items-center gap-3 rounded-md border px-3 py-2.5 transition-colors ${active ? 'border-cyan-400/20 bg-cyan-300/[.09] text-cyan-100' : 'border-transparent text-slate-400 hover:border-slate-700/80 hover:bg-slate-800/50 hover:text-slate-200'}`}
                >
                  <Icon size={16} strokeWidth={active ? 2.2 : 1.8} className={active ? 'text-cyan-300' : 'text-slate-500 group-hover:text-slate-300'} />
                  <span className="nav-label whitespace-nowrap text-[12px] font-semibold">{item.label}</span>
                  {item.href === '/incidents' && <span className="nav-label ml-auto rounded bg-red-400/15 px-1.5 py-0.5 font-mono text-[9px] text-red-300">3</span>}
                  {item.href === '/citizen-sos' && <span className="nav-label ml-auto rounded bg-amber-300/15 px-1.5 py-0.5 font-mono text-[9px] text-amber-300">2</span>}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [location] = useLocation();
  const current = (navGroups.flatMap((group) => [...group.items]) as Array<{ href: string; label: string }>).find((item) => item.href === location);
  return (
    <div className="shell-grid">
      <aside className={`sidebar fixed inset-y-0 left-0 z-40 flex w-[238px] flex-col border-r border-slate-800/80 bg-[#0b121d] ${mobileOpen ? 'block' : 'hidden'} lg:static lg:flex`}>
        <div className="flex items-center justify-between">
          <Mark />
          <button type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)} className="mr-3 rounded p-1.5 text-slate-500 hover:bg-slate-800 hover:text-slate-200 lg:hidden" data-testid="button-close-navigation"><X size={16} /></button>
        </div>
        <div className="mx-4 mb-4 border-y border-slate-800/80 py-3 sidebar-meta">
          <div className="flex items-center justify-between text-[10px] font-semibold text-slate-400"><span>OPERATING MODE</span><span className="text-cyan-300">LOCAL</span></div>
          <div className="mt-1.5 flex items-center gap-2 text-[10px] text-slate-500"><span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />Master available <span className="ml-auto font-mono">{new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span></div>
        </div>
        <Nav onNavigate={() => setMobileOpen(false)} />
        <div className="sidebar-meta m-3 rounded-md border border-slate-800 bg-slate-900/50 p-3">
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold text-slate-300"><CircleHelp size={13} className="text-slate-500" />Need operator support?</div>
          <p className="m-0 text-[10px] leading-relaxed text-slate-500">Reference the runbook before authorizing a response action.</p>
          <button type="button" className="mt-2 text-[10px] font-semibold text-cyan-300 hover:text-cyan-200" data-testid="button-open-runbook">Open runbook <span aria-hidden>→</span></button>
        </div>
      </aside>
      {mobileOpen && <button type="button" aria-label="Close navigation overlay" onClick={() => setMobileOpen(false)} className="fixed inset-0 z-30 bg-black/50 lg:hidden" data-testid="button-navigation-overlay" />}
      <div className="main-column">
        <header className="topbar flex items-center justify-between gap-4 px-3 sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <button type="button" aria-label="Open navigation" onClick={() => setMobileOpen(true)} className="rounded-md p-2 text-slate-400 hover:bg-slate-800 hover:text-slate-100 lg:hidden" data-testid="button-open-navigation"><Menu size={18} /></button>
            <div className="min-w-0">
              <div className="truncate text-[13px] font-bold text-slate-100">{current?.label || 'Authority dashboard'}</div>
              <div className="hidden truncate text-[10px] text-slate-500 sm:block">North County Emergency Operations Center <span className="px-1 text-slate-700">/</span> Operational picture</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="hidden items-center gap-2 rounded-md border border-slate-800 bg-slate-900/70 px-2.5 py-1.5 text-slate-500 md:flex">
              <Search size={14} />
              <input aria-label="Search dashboard" data-testid="input-global-search" placeholder="Search records" className="w-28 bg-transparent text-[11px] text-slate-200 outline-none placeholder:text-slate-600" />
              <span className="font-mono text-[9px] text-slate-700">⌘K</span>
            </label>
            <div className="hidden items-center gap-2 rounded-md border border-amber-400/20 bg-amber-400/[.06] px-2.5 py-1.5 text-[10px] font-semibold text-amber-200 sm:flex"><TriangleAlert size={13} />2 review items</div>
            <button type="button" aria-label="Open system settings" className="rounded-md p-2 text-slate-500 hover:bg-slate-800 hover:text-slate-100" data-testid="button-header-settings"><Settings2 size={16} /></button>
            <div className="grid h-7 w-7 place-items-center rounded-full border border-cyan-300/30 bg-cyan-300/10 font-mono text-[10px] font-bold text-cyan-200" title="Operator K. Lin">KL</div>
          </div>
        </header>
        <div className="status-strip app-scrollbar flex shrink-0 items-center gap-4 overflow-x-auto px-4 text-[10px] whitespace-nowrap">
          <span className="flex items-center gap-1.5 text-cyan-200"><span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />LOCAL MODE</span>
          <span className="text-slate-600">|</span>
          <span className="flex items-center gap-1.5 text-slate-400"><Radio size={12} className="text-cyan-400" />Master available</span>
          <span className="flex items-center gap-1.5 text-amber-200"><span className="h-1.5 w-1.5 rounded-full bg-amber-300" />Internet unavailable</span>
          <span className="flex items-center gap-1.5 text-slate-400"><Activity size={12} className="text-emerald-300" />Node ingest 96.4%</span>
          <span className="ml-auto hidden font-mono text-slate-500 md:block">SYNC FRAME {new Date().toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })} IST</span>
        </div>
        <main className="app-scrollbar min-h-0 flex-1 overflow-y-auto">{children}</main>
        <nav className="mobile-nav fixed bottom-0 left-0 right-0 z-20 hidden items-center justify-around border-t border-slate-800 bg-[#0b121d]/95 p-2 backdrop-blur-md">
          <Link href="/overview" className="rounded p-2 text-cyan-300" data-testid="link-mobile-overview"><Command size={18} /></Link>
          <Link href="/incidents" className="rounded p-2 text-slate-400" data-testid="link-mobile-incidents"><ShieldAlert size={18} /></Link>
          <Link href="/nodes" className="rounded p-2 text-slate-400" data-testid="link-mobile-nodes"><Boxes size={18} /></Link>
          <Link href="/response" className="rounded p-2 text-slate-400" data-testid="link-mobile-response"><Cable size={18} /></Link>
        </nav>
      </div>
    </div>
  );
}