import { type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import NotFound from '@/pages/not-found';
import { Shell } from '@/components/nexalert/Shell';
import { OverviewPageLive } from '@/pages/overview-live';
import { NodesPageLive } from '@/pages/nodes-live';
import { TelemetryPageLive } from '@/pages/telemetry-live';
import { IncidentsPageLive } from '@/pages/incidents-live';
import { FireSpreadPageLive } from '@/pages/fire-spread-live';
import { MultiHazardPageLive } from '@/pages/multi-hazard-live';
import { AffectedAreaPageUnavailable } from '@/pages/affected-area-unavailable';
import { HistoricalPageUnavailable } from '@/pages/historical-unavailable';
import {
  CitizenSOSPageUnavailable,
  AlertsPageUnavailable,
  ResponsePageUnavailable,
  AuditPageUnavailable,
  SystemPageLive,
} from '@/pages/unavailable-pages';
import {
  Route,
  Switch,
  Router as WouterRouter,
  Redirect,
  useLocation,
} from 'wouter';

const queryClient = new QueryClient();

function Router() {
  return (
    // Keep a shared shell (sidebar, navbar) outside the boundary so it
    // survives a page crash.
    <RoutedErrorBoundary>
      <Shell>
        <Switch>
          <Route path="/" component={() => <Redirect to="/overview" />} />
          <Route path="/overview" component={OverviewPageLive} />
          <Route path="/incidents" component={IncidentsPageLive} />
          <Route path="/fire-spread" component={FireSpreadPageLive} />
          <Route path="/affected-area" component={AffectedAreaPageUnavailable} />
          <Route path="/multi-hazard" component={MultiHazardPageLive} />
          <Route path="/nodes" component={NodesPageLive} />
          <Route path="/telemetry" component={TelemetryPageLive} />
          <Route path="/citizen-sos" component={CitizenSOSPageUnavailable} />
          <Route path="/alerts" component={AlertsPageUnavailable} />
          <Route path="/historical" component={HistoricalPageUnavailable} />
          <Route path="/response" component={ResponsePageUnavailable} />
          <Route path="/audit" component={AuditPageUnavailable} />
          <Route path="/system" component={SystemPageLive} />
          <Route component={NotFound} />
        </Switch>
      </Shell>
    </RoutedErrorBoundary>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
          <Router />
        </WouterRouter>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
